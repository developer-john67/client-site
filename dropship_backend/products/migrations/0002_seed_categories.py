from django.db import migrations


def create_categories(apps, schema_editor):
    Category = apps.get_model('products', 'Category')
    
    categories = [
        {'name': 'Electronics', 'slug': 'electronics'},
        {'name': 'Clothing & Apparel', 'slug': 'clothing-apparel'},
        {'name': 'Home & Garden', 'slug': 'home-garden'},
        {'name': 'Sports & Outdoor', 'slug': 'sports-outdoor'},
        {'name': 'Beauty & Health', 'slug': 'beauty-health'},
        {'name': 'Books & Media', 'slug': 'books-media'},
        {'name': 'Games & Toys', 'slug': 'games-toys'},
        {'name': 'Automotive', 'slug': 'automotive'},
        {'name': 'Food & Groceries', 'slug': 'food-groceries'},
        {'name': 'Other', 'slug': 'other'},
    ]
    
    for cat in categories:
        Category.objects.get_or_create(slug=cat['slug'], defaults={'name': cat['name']})


def remove_categories(apps, schema_editor):
    Category = apps.get_model('products', 'Category')
    Category.objects.filter(slug__in=[
        'electronics', 'clothing-apparel', 'home-garden', 'sports-outdoor',
        'beauty-health', 'books-media', 'games-toys', 'automotive',
        'food-groceries', 'other'
    ]).delete()


class Migration(migrations.Migration):
    dependencies = [
        ('products', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_categories, remove_categories),
    ]
