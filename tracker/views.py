import json
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from .forms import ExpenseForm
from .models import Expense
from django.db.models import Sum
from .forms import RegisterForm
from .forms import DateRangeForm
from django.utils import timezone
from datetime import timedelta
from datetime import datetime
from django.contrib.auth import login

@login_required
def spending_chart(request):
    expenses = Expense.objects.filter(user=request.user).order_by('date')
    labels = [e.date.strftime('%Y-%m-%d') for e in expenses]
    data = [float(e.amount) for e in expenses]
    return render(request, 'spending_chart.html', {
        'labels': json.dumps(labels),
        'data': json.dumps(data)
    })

def home(request):
    return render(request, 'home.html')

def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()  # ✅ Save user to the database
            login(request, user)  # (Optional) Log the user in after registration
            return redirect('home')  # Change to your desired redirect
    else:
        form = UserCreationForm()
    
    return render(request, 'register.html', {'form': form})

@login_required
def dashboard(request):
    expenses = Expense.objects.filter(user=request.user)
    total = 0

    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    if start_date and end_date:
        expenses = expenses.filter(date__range=[start_date, end_date])

    total = sum(e.amount for e in expenses)

    return render(request, 'dashboard.html', {
        'expenses': expenses,
        'total': total
    })


@login_required
def split_expenses(request):
    result = None
    people = []
    num_people = 2
    total_amount = ''
    if request.method == 'POST':
        num_people = int(request.POST.get('num_people', 2))
        total_amount = request.POST.get('total_amount', '')
        try:
            total_amount_float = float(total_amount)
        except (ValueError, TypeError):
            total_amount_float = 0
        people = []
        for i in range(num_people):
            name = request.POST.get(f'name_{i}', f'Person {i+1}')
            try:
                contribution = float(request.POST.get(f'contribution_{i}', 0))
            except ValueError:
                contribution = 0
            people.append({'name': name, 'contribution': contribution})
        if num_people > 0 and total_amount_float > 0:
            split_amount = total_amount_float / num_people
            for p in people:
                p['balance'] = round(p['contribution'] - split_amount, 2)
                p['abs_balance'] = abs(p['balance'])
            result = {
                'total': total_amount_float,
                'split_amount': round(split_amount, 2),
                'people': people
            }
    people_range = range(num_people)
    return render(request, 'split_expenses.html', {'result': result, 'people': people, 'people_range': people_range, 'num_people': num_people, 'total_amount': total_amount})
@login_required
def add_expense(request):
    if request.method == 'POST':
        form = ExpenseForm(request.POST)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.user = request.user
            expense.save()
            return redirect('dashboard')
    else:
        form = ExpenseForm()
    return render(request, 'add_expense.html', {'form': form})

@login_required
def delete_expense(request, pk):
    expense = Expense.objects.get(pk=pk, user=request.user)
    expense.delete()
    return redirect('dashboard')
