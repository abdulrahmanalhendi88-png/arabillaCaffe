from django.db import models
from django.utils import timezone
from django.utils.text import slugify


class Category(models.Model):
    name = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(max_length=90, unique=True, db_index=True)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["order", "name"]

    def __str__(self) -> str:
        return self.name


class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="products")
    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140, unique=True, db_index=True)
    description = models.CharField(max_length=220, blank=True)
    price_syp = models.PositiveIntegerField()
    image = models.ImageField(upload_to="products/", blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)

    class Meta:
        ordering = ["-is_featured", "name"]

    def __str__(self) -> str:
        return self.name


class Offer(models.Model):
    title = models.CharField(max_length=140)
    subtitle = models.CharField(max_length=180, blank=True)
    price_syp = models.PositiveIntegerField()
    image = models.ImageField(upload_to="offers/", blank=True, null=True)
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    # slug لازم يكون موجود ومميز
    slug = models.SlugField(max_length=140, unique=True, db_index=True, blank=True)

    class Meta:
        ordering = ["order", "title"]

    def save(self, *args, **kwargs):
        """
        ✅ توليد slug تلقائياً بشكل آمن وفريد
        - مرة واحدة فقط
        - بدون super مرتين
        """
        if not self.slug:
            base = slugify(self.title) or "offer"
            candidate = base
            i = 2
            # تأكد من uniqueness
            while Offer.objects.filter(slug=candidate).exclude(pk=self.pk).exists():
                candidate = f"{base}-{i}"
                i += 1
            self.slug = candidate

        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.title


class Order(models.Model):
    class Status(models.TextChoices):
        NEW = "new", "NEW"
        PREPARING = "preparing", "PREPARING"
        READY = "ready", "READY"
        DELIVERED = "delivered", "DELIVERED"
        CANCELED = "canceled", "CANCELED"

    table_no = models.CharField(max_length=20, db_index=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.NEW)
    note = models.CharField(max_length=400, blank=True)
    total_syp = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"Order #{self.id} - Table {self.table_no}"


class OrderItem(models.Model):
    class ItemType(models.TextChoices):
        PRODUCT = "product", "PRODUCT"
        OFFER = "offer", "OFFER"

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")

    item_type = models.CharField(max_length=20, choices=ItemType.choices, default=ItemType.PRODUCT)

    # واحد منهم فقط يجب أن يكون موجود حسب item_type
    product = models.ForeignKey(Product, on_delete=models.PROTECT, null=True, blank=True)
    offer = models.ForeignKey(Offer, on_delete=models.PROTECT, null=True, blank=True)

    name_snapshot = models.CharField(max_length=140)
    price_syp_snapshot = models.PositiveIntegerField()
    qty = models.PositiveIntegerField(default=1)

    # ملاحظات تخصيص لكل سطر (خصوصاً للعروض)
    note_snapshot = models.CharField(max_length=400, blank=True)

    @property
    def line_total(self) -> int:
        return int(self.price_syp_snapshot) * int(self.qty)

    def __str__(self) -> str:
        return f"{self.name_snapshot} x{self.qty}"
