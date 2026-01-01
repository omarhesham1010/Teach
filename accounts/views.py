from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from .models import User

# Extend UserCreationForm to use our custom User model behavior if needed,
# or just use the default one but ensure it works with custom auth model.
# For simplicity in Phase 1, we use a basic form wrapper or the default if compatible.
# Since we have a custom user model, we should use a custom form ideally, 
# but UserCreationForm works if configured in settings (which we did).

# Actually, standard UserCreationForm needs mapped to the custom model.
from django.contrib.auth.forms import UserCreationForm as BaseUserCreationForm

class CustomUserCreationForm(BaseUserCreationForm):
    class Meta:
        model = User
        fields = ("username", "email")

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = CustomUserCreationForm()
    return render(request, 'accounts/register.html', {'form': form})
