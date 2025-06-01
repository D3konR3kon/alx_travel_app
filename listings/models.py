# listings/models.py
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal


class Listing(models.Model):
    PROPERTY_TYPES = [
        ('house', 'House'),
        ('apartment', 'Apartment'),
        ('condo', 'Condo'),
        ('villa', 'Villa'),
        ('cabin', 'Cabin'),
        ('other', 'Other'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    location = models.CharField(max_length=200)
    price_per_night = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    number_of_bedrooms = models.PositiveIntegerField(default=1)
    number_of_bathrooms = models.PositiveIntegerField(default=1)
    max_guests = models.PositiveIntegerField(default=1)
    property_type = models.CharField(
        max_length=20, 
        choices=PROPERTY_TYPES, 
        default='apartment'
    )
    amenities = models.TextField(
        help_text="Comma-separated list of amenities",
        blank=True
    )
    availability = models.BooleanField(default=True)
    host = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='listings'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['location']),
            models.Index(fields=['price_per_night']),
            models.Index(fields=['availability']),
        ]
        
    def __str__(self):
        return f"{self.title} - {self.location}"
    
    @property
    def average_rating(self):
        reviews = self.reviews.all()
        if reviews:
            return sum(review.rating for review in reviews) / len(reviews)
        return 0


class Booking(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    ]
    
    listing = models.ForeignKey(
        Listing, 
        on_delete=models.CASCADE, 
        related_name='bookings'
    )
    guest = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='bookings'
    )
    check_in_date = models.DateField()
    check_out_date = models.DateField()
    number_of_guests = models.PositiveIntegerField()
    total_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='pending'
    )
    special_requests = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
class Meta:
    ordering = ['-created_at']
    indexes = [
        models.Index(fields=['check_in_date', 'check_out_date']),
        models.Index(fields=['status']),
    ]
    constraints = [
        models.CheckConstraint(
            check=models.Q(check_out_date__gt=models.F('check_in_date')),
            name='check_out_after_check_in'
        ),
    ]
        
    def __str__(self):
        return f"Booking {self.id} - {self.listing.title}"
    
    def save(self, *args, **kwargs):
    # Calculate total_price if not set or is None
        if not self.total_price or self.total_price is None:
            days = (self.check_out_date - self.check_in_date).days
            self.total_price = self.listing.price_per_night * days
        super().save(*args, **kwargs)


class Review(models.Model):
    listing = models.ForeignKey(
        Listing, 
        on_delete=models.CASCADE, 
        related_name='reviews'
    )
    reviewer = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='reviews'
    )
    booking = models.OneToOneField(
        Booking, 
        on_delete=models.CASCADE, 
        related_name='review',
        null=True, 
        blank=True
    )
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['listing', 'reviewer']
        indexes = [
            models.Index(fields=['rating']),
        ]
        
    def __str__(self):
        return f"Review by {self.reviewer.username} for {self.listing.title} - {self.rating}/5"