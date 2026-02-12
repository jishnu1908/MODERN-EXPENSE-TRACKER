from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib import messages
from django.db.models import Sum, Count
from django.db.models.functions import TruncMonth
from datetime import datetime, timedelta
from .models import Expense, Category
from .forms import UserRegisterForm, ExpenseForm, CategoryForm


class CustomLoginView(LoginView):
    template_name = 'registration/login.html'


def register(request):
    """User registration view"""
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Create default categories for new user
            default_categories = [
                {'name': 'Food', 'icon': '🍔', 'color': '#ef4444'},
                {'name': 'Transport', 'icon': '🚗', 'color': '#3b82f6'},
                {'name': 'Shopping', 'icon': '🛍️', 'color': '#ec4899'},
                {'name': 'Entertainment', 'icon': '🎬', 'color': '#8b5cf6'},
                {'name': 'Bills', 'icon': '📄', 'color': '#f59e0b'},
                {'name': 'Health', 'icon': '⚕️', 'color': '#10b981'},
            ]
            for cat_data in default_categories:
                Category.objects.create(user=user, **cat_data)
            
            login(request, user)
            messages.success(request, f'Account created successfully! Welcome, {user.username}!')
            return redirect('dashboard')
    else:
        form = UserRegisterForm()
    return render(request, 'registration/register.html', {'form': form})


@login_required
def dashboard(request):
    """Dashboard view with expense statistics"""
    user_expenses = Expense.objects.filter(user=request.user)
    
    # Calculate statistics
    total_expenses = user_expenses.filter(transaction_type='EXPENSE').aggregate(total=Sum('amount'))['total'] or 0
    total_receivables = user_expenses.filter(transaction_type='RECEIVABLE').aggregate(total=Sum('amount'))['total'] or 0
    
    # Current month expenses
    today = datetime.now()
    month_start = today.replace(day=1)
    month_expenses = user_expenses.filter(
        transaction_type='EXPENSE',
        date__gte=month_start
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    # Category breakdown (Expenses only)
    category_stats = user_expenses.filter(transaction_type='EXPENSE').values('category__name', 'category__icon', 'category__color').annotate(
        total=Sum('amount'),
        count=Count('id')
    ).order_by('-total')[:6]
    
    # Recent transactions
    recent_expenses = user_expenses[:5]
    
    # Monthly trend (last 6 months - Expenses only)
    six_months_ago = today - timedelta(days=180)
    monthly_data = user_expenses.filter(
        transaction_type='EXPENSE',
        date__gte=six_months_ago
    ).annotate(
        month=TruncMonth('date')
    ).values('month').annotate(total=Sum('amount')).order_by('month')
    
    context = {
        'total_expenses': total_expenses,
        'total_receivables': total_receivables,
        'month_expenses': month_expenses,
        'category_stats': category_stats,
        'recent_expenses': recent_expenses,
        'monthly_data': monthly_data,
        'expense_count': user_expenses.filter(transaction_type='EXPENSE').count(),
        'receivable_count': user_expenses.filter(transaction_type='RECEIVABLE').count(),
    }
    return render(request, 'expenses/dashboard.html', context)


@login_required
def expense_list(request):
    """List all transactions with filtering"""
    expenses = Expense.objects.filter(user=request.user)
    
    # Filters
    category_id = request.GET.get('category')
    transaction_type = request.GET.get('type')
    payment_method = request.GET.get('payment_method')
    search = request.GET.get('search')
    
    if category_id:
        expenses = expenses.filter(category_id=category_id)
    if transaction_type:
        expenses = expenses.filter(transaction_type=transaction_type)
    if payment_method:
        expenses = expenses.filter(payment_method=payment_method)
    if search:
        expenses = expenses.filter(title__icontains=search)
    
    categories = Category.objects.filter(user=request.user)
    
    context = {
        'expenses': expenses,
        'categories': categories,
        'transaction_types': Expense.TRANSACTION_TYPE_CHOICES,
        'payment_methods': Expense.PAYMENT_METHOD_CHOICES,
        'selected_category': category_id,
        'selected_type': transaction_type,
        'selected_payment': payment_method,
        'search_query': search or '',
    }
    return render(request, 'expenses/expense_list.html', context)


@login_required
def expense_create(request):
    """Create new expense"""
    if request.method == 'POST':
        form = ExpenseForm(request.POST)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.user = request.user
            expense.save()
            messages.success(request, 'Expense added successfully!')
            return redirect('dashboard')
    else:
        form = ExpenseForm()
    
    # Filter categories for current user
    form.fields['category'].queryset = Category.objects.filter(user=request.user)
    return render(request, 'expenses/expense_form.html', {'form': form, 'title': 'Add Expense'})


import csv
from django.http import HttpResponse

@login_required
def export_expenses_csv(request):
    """Export expenses to CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="expenses_{datetime.now().strftime("%Y%m%d")}.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Date', 'Title', 'Category', 'Amount', 'Description'])
    
    expenses = Expense.objects.filter(user=request.user)
    for expense in expenses:
        writer.writerow([
            expense.date,
            expense.title,
            expense.category.name if expense.category else 'No Category',
            expense.amount,
            expense.description
        ])
    
    return response


@login_required
def expense_update(request, pk):
    """Update existing expense"""
    expense = get_object_or_404(Expense, pk=pk, user=request.user)
    
    if request.method == 'POST':
        form = ExpenseForm(request.POST, instance=expense)
        if form.is_valid():
            form.save()
            messages.success(request, 'Expense updated successfully!')
            return redirect('expense_list')
    else:
        form = ExpenseForm(instance=expense)
    
    form.fields['category'].queryset = Category.objects.filter(user=request.user)
    return render(request, 'expenses/expense_form.html', {'form': form, 'title': 'Edit Expense'})


@login_required
def expense_delete(request, pk):
    """Delete expense"""
    expense = get_object_or_404(Expense, pk=pk, user=request.user)
    
    if request.method == 'POST':
        expense.delete()
        messages.success(request, 'Expense deleted successfully!')
        return redirect('expense_list')
    
    return render(request, 'expenses/expense_confirm_delete.html', {'expense': expense})


@login_required
def category_list(request):
    """List all categories"""
    categories = Category.objects.filter(user=request.user)
    return render(request, 'expenses/category_list.html', {'categories': categories})


@login_required
def category_create(request):
    """Create new category"""
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = form.save(commit=False)
            category.user = request.user
            category.save()
            messages.success(request, 'Category created successfully!')
            return redirect('category_list')
    else:
        form = CategoryForm()
    
    return render(request, 'expenses/category_form.html', {'form': form, 'title': 'Add Category'})


@login_required
def category_update(request, pk):
    """Update existing category"""
    category = get_object_or_404(Category, pk=pk, user=request.user)
    
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category updated successfully!')
            return redirect('category_list')
    else:
        form = CategoryForm(instance=category)
    
    return render(request, 'expenses/category_form.html', {'form': form, 'title': 'Edit Category'})


@login_required
def category_delete(request, pk):
    """Delete category"""
    category = get_object_or_404(Category, pk=pk, user=request.user)
    
    if request.method == 'POST':
        category.delete()
        messages.success(request, 'Category deleted successfully!')
        return redirect('category_list')
    
    return render(request, 'expenses/category_confirm_delete.html', {'category': category})
