import json
from django.contrib.auth import authenticate, login as django_login
from django.contrib.auth.models import User
from django.db import connection
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .models import Product, Comment, AuditLog
from .auth import issue_token, user_from_token

def json_error(msg, status=400):
    return JsonResponse({'error': msg}, status=status)

def get_json_body(request):
    try:
        return json.loads(request.body or b'{}')
    except json.JSONDecodeError:
        return {}

# ================= AUTH =================

@csrf_exempt
@require_http_methods(['POST'])
def api_login(request):
    """VULN: credentials concatenated into raw SQL -> auth bypass.
    Also VULN: raw DB errors leaked in response."""
    body = get_json_body(request)
    u = str(body.get('username', ''))
    p = str(body.get('password', ''))
    sql = f"SELECT id, username FROM auth_user WHERE username='{u}' AND password='{p}'"
    try:
        with connection.cursor() as cur:
            cur.execute(sql)
            row = cur.fetchone()
    except Exception as e:
        return JsonResponse({'error': 'database_error', 'detail': str(e)}, status=500)
    if not row:
        return json_error('invalid credentials', 401)
    user = User.objects.get(id=row[0])
    django_login(request, user)          # real session after (injected) match
    token = issue_token(user)
    AuditLog.objects.create(action='login', detail=f'user={row[1]}')
    return JsonResponse({'token': token, 'username': row[1]})

# ================= PRODUCTS =================

@csrf_exempt
def vuln_products(request):
    """GET /api/vuln/products/?q=&category=
    VULN: q and category concatenated into SQL. UNION extraction target."""
    q = request.GET.get('q', '')
    category = request.GET.get('category', '')
    sql = ("SELECT id, name, price, category FROM api_product "
           f"WHERE name LIKE '%{q}%' OR description LIKE '%{q}%'")
    if category:
        sql += f" AND category = '{category}'"
    try:
        with connection.cursor() as cur:
            cur.execute(sql)
            rows = cur.fetchall()
    except Exception as e:
        return JsonResponse({'error': 'database_error', 'detail': str(e)}, status=500)
    return JsonResponse({'count': len(rows), 'results': [
        {'id': r[0], 'name': r[1], 'price': str(r[2]), 'category': r[3]} for r in rows
    ]})

@csrf_exempt
def safe_products(request):
    """GET /api/safe/products/?q=
    SAFE: parameterized query (control group)."""
    q = request.GET.get('q', '')
    sql = ("SELECT id, name, price, category FROM api_product "
           "WHERE name LIKE %s OR description LIKE %s")
    with connection.cursor() as cur:
        cur.execute(sql, [f'%{q}%', f'%{q}%'])
        rows = cur.fetchall()
    return JsonResponse({'count': len(rows), 'results': [
        {'id': r[0], 'name': r[1], 'price': str(r[2]), 'category': r[3]} for r in rows
    ]})

@csrf_exempt
def vuln_product_detail(request, product_id):
    """GET /api/vuln/products/<id>/
    VULN: numeric URL parameter interpolated raw -> numeric injection.
    Also VULN: NO AUTH CHECK at all (unauthenticated data access)."""
    sql = (f"SELECT id, name, description, price, category, owner_id "
           f"FROM api_product WHERE id = {product_id}")
    try:
        with connection.cursor() as cur:
            cur.execute(sql)
            row = cur.fetchone()
    except Exception as e:
        return JsonResponse({'error': 'database_error', 'detail': str(e)}, status=500)
    if not row:
        return json_error('not found', 404)
    return JsonResponse({'id': row[0], 'name': row[1], 'description': row[2],
                         'price': str(row[3]), 'category': row[4], 'owner_id': row[5]})

@csrf_exempt
@require_http_methods(['POST'])
def vuln_product_create(request):
    """POST /api/vuln/products/create/
    VULN 1: mass assignment — client sets 'owner_id' and 'is_featured'-style fields.
    VULN 2: SQL injection via 'category'/'name' values (built by string concat)."""
    user = user_from_token(request.headers.get('Authorization'))
    if not user:
        return json_error('authentication required', 401)
    body = get_json_body(request)
    name = str(body.get('name', ''))
    desc = str(body.get('description', ''))
    price = str(body.get('price', '0'))
    category = str(body.get('category', ''))
    # VULN: mass assignment — client can claim any owner_id
    owner_id = body.get('owner_id', user.id)
    sql = (f"INSERT INTO api_product (name, description, price, category, owner_id) "
           f"VALUES ('{name}', '{desc}', {price}, '{category}', {owner_id})")
    try:
        with connection.cursor() as cur:
            cur.execute(sql)
            new_id = cur.lastrowid
    except Exception as e:
        return JsonResponse({'error': 'database_error', 'detail': str(e)}, status=500)
    AuditLog.objects.create(action='product_create', detail=f'by={user.username}')
    return JsonResponse({'id': new_id, 'message': 'created'}, status=201)

# ================= PROFILE / IDOR =================

@csrf_exempt
def vuln_profile(request):
    """GET /api/vuln/profile/?id=<n>
    VULN 1: no ownership check — any authenticated user can read ANY user (IDOR).
    VULN 2: id is injected into raw SQL."""
    user = user_from_token(request.headers.get('Authorization'))
    if not user:
        return json_error('authentication required', 401)
    uid = request.GET.get('id', str(user.id))
    sql = f"SELECT id, username, email, first_name, last_name FROM auth_user WHERE id = {uid}"
    try:
        with connection.cursor() as cur:
            cur.execute(sql)
            row = cur.fetchone()
    except Exception as e:
        return JsonResponse({'error': 'database_error', 'detail': str(e)}, status=500)
    if not row:
        return json_error('not found', 404)
    return JsonResponse({'id': row[0], 'username': row[1], 'email': row[2],
                         'first_name': row[3], 'last_name': row[4]})

# ================= SEARCH LOG (blind injection / exfil channel) =================

@csrf_exempt
def vuln_admin_stats(request):
    """GET /api/vuln/admin/stats?filter=
    VULN: 'filter' concatenated into SQL; no role check.
    Response is only true/false -> boolean-blind injection practice."""
    f = request.GET.get('filter', '')
    sql = f"SELECT COUNT(*) FROM api_auditlog WHERE action LIKE '%{f}%'"
    try:
        with connection.cursor() as cur:
            cur.execute(sql)
            n = cur.fetchone()[0]
    except Exception:
        return JsonResponse({'result': False})
    return JsonResponse({'result': n > 0})

# ================= COMMENTS (normal, safe CRUD for realism) =================

@csrf_exempt
@require_http_methods(['POST'])
def comment_create(request, product_id):
    user = user_from_token(request.headers.get('Authorization'))
    if not user:
        return json_error('authentication required', 401)
    body = get_json_body(request)
    try:
        product = Product.objects.get(id=int(product_id))
    except (Product.DoesNotExist, ValueError):
        return json_error('product not found', 404)
    c = Comment.objects.create(product=product, author=user, body=str(body.get('body', ''))[:2000])
    return JsonResponse({'id': c.id, 'body': c.body}, status=201)