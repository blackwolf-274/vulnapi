from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from api.models import Product, Comment

class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        users = {}
        for u, p in [('admin', 'S3cr3tAdmin!'), ('alice', 'AlicePass123'), ('bob', 'BobPass456')]:
            users[u], _ = User.objects.get_or_create(
                username=u, defaults={'email': f'{u}@vulnapi.local'})
            users[u].set_password(p)
            users[u].save()
        data = [
            ('Laptop Pro 15', 'High-end laptop, 16GB RAM.', '1299.99', 'Electronics', 'admin'),
            ('Wireless Mouse', 'Ergonomic 2.4GHz mouse.', '24.50', 'Electronics', 'alice'),
            ('Coffee Maker', '12-cup programmable.', '79.00', 'Home', 'bob'),
            ('Running Shoes', 'Marathon training shoes.', '89.99', 'Sports', 'alice'),
        ]
        for name, desc, price, cat, owner in data:
            prod, _ = Product.objects.get_or_create(
                name=name, defaults={'description': desc, 'price': price,
                                     'category': cat, 'owner': users[owner]})
            Comment.objects.get_or_create(product=prod, author=users['bob'],
                                          body=f'Review of {name}')
        self.stdout.write('Seeded.')