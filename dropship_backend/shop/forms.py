from django import forms


def get_category_choices():
    """Load categories from database at runtime."""
    try:
        from products.models import Category
        cats = list(Category.objects.filter(is_active=True))
        choices = [('', '— Select a category —')]
        for c in sorted(cats, key=lambda x: x.name):
            choices.append((str(c.category_id), c.name))
        return choices
    except Exception:
        return [
            ('', '— Select a category —'),
            ('electronics',      'Electronics'),
            ('clothing-apparel', 'Clothing & Apparel'),
            ('home-garden',      'Home & Garden'),
            ('sports-outdoor',   'Sports & Outdoor'),
            ('beauty-health',    'Beauty & Health'),
            ('books-media',      'Books & Media'),
            ('games-toys',       'Games & Toys'),
            ('automotive',       'Automotive'),
            ('food-groceries',   'Food & Groceries'),
            ('other',            'Other'),
        ]


class ProductUploadForm(forms.Form):
    name = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Enter product name'
        })
    )
    description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-input',
            'placeholder': 'Describe your product...',
            'rows': 4
        })
    )
    price = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-input',
            'placeholder': '0.00',
            'step': '0.01',
            'min': '0'
        })
    )
    category = forms.ChoiceField(
        widget=forms.Select(attrs={'class': 'form-input'})
    )
    stock_quantity = forms.IntegerField(
        min_value=0,
        initial=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-input',
            'placeholder': '0',
            'min': '0'
        })
    )
    image = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-input file-input',
            'accept': 'image/*'
        })
    )
    is_active = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-checkbox'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].choices = get_category_choices()