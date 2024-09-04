from django.shortcuts import render
from rest_framework.views import View
from .models import Product,Customer,Cart
from.forms import CustomerRegistrationForm
from django.db.models import Count
from django.contrib import messages
from django.shortcuts import redirect
from django.shortcuts import get_object_or_404
from django.http import HttpResponseBadRequest, HttpResponseNotFound, JsonResponse
from django.db.models import Q




from django.contrib.auth.views import PasswordChangeView
from . forms import LoginForm ,MyPasswordResetForm,CustomerProfileForm,MyPasswordChangeForm
# Create your views here.

from django.http import HttpResponse



def base(request):
    return render(request,'app/base.html')

def home(request):
    return render(request,'app/home.html')


def about(request):
    return render(request,'app/about.html')


def contact(request):
    return render(request,'app/contact.html')



class CategoryView(View):

    def get(self,request,val):
         product = Product.objects.filter(category=val)
         title = Product.objects.filter(category=val).values('title').annotate(total=Count('title'))
         return render(request,'app/category.html',locals())
    
class CategoryTitle(View):
    def get(self,request,val):
        product=Product.objects.filter(title=val)
        title = Product.objects.filter(category=product[0].category).values('title')
        return render(request,'app/category.html',locals())
class ProductDetail(View):
    def get(self,request,pk):
        product = Product.objects.get(pk=pk)
        return render(request,'app/productdetail.html',locals()) 



class CustomerRegistrationView(View):
    def get(self,request):
        form = CustomerRegistrationForm()
        return render(request,'app/customerregistration.html',locals())

    
    def post(self,request):
        form = CustomerRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request,"Congratulations ! User Register Succcessfully")

        else:
            messages.warning(request,"Invalid Input Data") 
        return render(request,'app/customerregistration.html',locals())


class ProfileView(View):
    def get(self,request):
        form = CustomerProfileForm()
        return render(request,'app/profile.html',locals())
    
    def post(self,request):
        form = CustomerProfileForm(request.POST)
        if form.is_valid():
            user = request.user
            name = form.cleaned_data['name']
            locality = form.cleaned_data['locality']
            city = form.cleaned_data['city']
            mobile = form.cleaned_data['mobile']
            pincode = form.cleaned_data['pincode']
            reg = Customer(user=user,name=name,locality=locality,mobile=mobile,city=city,pincode=pincode)
            reg.save()

        else:
            messages.warning(request,"Invalid Input Data ")    
        return render(request,'app/profile.html',locals())
    



def address(request):
    add = Customer.objects.filter(user=request.user)
    return render(request,'app/address.html',locals())



class updateAddress(View):
    def get(self,request,pk):
        add=Customer.objects.get(pk=pk)
        form = CustomerProfileForm(instance=add)
        return render(request,'app/updateAddress.html',locals())

    def post(self,request,pk):
         form = CustomerProfileForm(request.POST)
         if form.is_valid():
             add = Customer.objects.get(pk=pk)
             add.name = form.cleaned_data['name']
             add.locality = form.cleaned_data['locality']
             add.city = form.cleaned_data['city']
             add.mobile = form.cleaned_data['mobile']
             add.pincode = form.cleaned_data['pincode']
             add.save()
             messages.success(request,"Congratulations ! Profile Update Successfully ")
         else:
             messages.success(request,"Invalid Input Data")
             
         return render(request,'app/updateAddress.html',locals())

        


# def add_to_cart(request):
#     user = request.user
#     product_id = request.GET.get('prod_id')

#     product = Product.objects.get(id=product_id)
#     Cart(user=user,product=product).save()
#     return redirect('/cart')

def add_to_cart(request):
    user = request.user
    product_id = request.GET.get('prod_id', '').rstrip('/')  # Remove trailing slashes
    if not product_id.isdigit():
        return HttpResponseBadRequest("Invalid product ID")

    try:
        product_id = int(product_id)
        product = Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        return HttpResponseNotFound("Product not found")
    except ValueError:
        return HttpResponseBadRequest("Invalid product ID")

    Cart(user=user, product=product).save()
    return redirect('/app/cart')



def show_cart(request):
    user = request.user
    cart = Cart.objects.filter(user=user)
    amount = 0
    for p in cart:
        value = p.quantity*p.product.discounted_price
        amount = amount + value
    totalamount = amount + 40    
    return render(request,'app/addtocart.html',locals())


# class Checkout(View):
#     def get(self,request):
#         user=request.user
#         add =Customer.objects.filter(user=user)
#         cart_items = Cart.objects.filter(user=user)
#         amount=0
#         for p in cart_items:
#             value = p.quantity * p.product.discounted_price
#             amount=amount + value
#         totalamount = amount+40    
#         return render(request,'app/checkout.html',locals())
class Checkout(View):
    def get(self, request):
        user = request.user
        # Fetch addresses and cart items for the user
        add = Customer.objects.filter(user=user)
        cart_items = Cart.objects.filter(user=user)
        
        # Calculate total amount
        amount = 0
        for p in cart_items:
            value = p.quantity * p.product.discounted_price
            amount += value
        totalamount = amount + 40  # Add fixed shipping cost
        
        # Pass context to the template
        context = {
            'add': add,
            'cart_items': cart_items,
            'totalamount': totalamount
        }
        
        return render(request, 'app/checkout.html', context)

# def plus_cart(request):
#     if request.method == "GET":
#         prod_id = request.GET['prod_id']
#         c = Cart.objects.get(Q(product=prod_id) & Q(user=request.user))
#         c.quantity+=1
#         c.save()
#         user = request.user
#         cart= Cart.objects.filter(user=user)

#         amount = 0
#         for p in cart:
#             value = p.quantity*p.product.discounted_price
#             amount = amount + value
#         totalamount = amount + 40
#         data={
#          'quantity':c.quantity,
#          'amount':amount,
#          'totalamount':totalamount
#         }

#         return JsonResponse(data)
    

from django.http import JsonResponse
from django.db.models import Q

def plus_cart(request):
    if request.method == "GET":
        prod_id = request.GET.get('prod_id')

        if not prod_id:
            return JsonResponse({'error': 'Product ID not provided'}, status=400)

        # Get all Cart items that match the criteria
        carts = Cart.objects.filter(Q(product_id=prod_id) & Q(user=request.user))

        if not carts.exists():
            return JsonResponse({'error': 'Cart item not found'}, status=404)

        # If multiple carts are found, handle them as needed
        cart = carts.first()  # Or implement custom logic to handle multiple carts

        # Increase quantity
        cart.quantity += 1
        cart.save()

        # Calculate new amounts
        user = request.user
        cart_items = Cart.objects.filter(user=user)

        amount = sum(item.quantity * item.product.discounted_price for item in cart_items)
        totalamount = amount + 40  # Assuming a fixed shipping fee

        data = {
            'quantity': cart.quantity,
            'amount': amount,
            'totalamount': totalamount
        }

        return JsonResponse(data)



# def minus_cart(request):
#     if request.method=="GET":
#         prod_id=request.GET['prod_id']
#         c = Cart.objects.get(Q(product=prod_id)& Q(user=request.user))
#         c.quantity-=1
#         c.save()
#         user=request.user
#         cart = Cart.objects.filter(user=user)
#         amount=0
#         for p in cart:
#             value = p.quantity*p.product.discounted_price
#             amount=amount+value
#         totalamount=amount+40

#         data={
#             'quantity':c.quantity,
#              'amount':amount,
#              'totalamount':totalamount
#         }    
        
#         return JsonResponse(data)
    
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from .models import Cart
from django.db.models import Q

def minus_cart(request):
    if request.method == "GET":
        prod_id = request.GET.get('prod_id')
        
        if not prod_id:
            # Log the request for debugging
            print(f"Request GET parameters: {request.GET}")
            return JsonResponse({'error': 'prod_id parameter is missing'}, status=400)
        
        try:
            c = Cart.objects.get(Q(product=prod_id) & Q(user=request.user))
        except Cart.DoesNotExist:
            return JsonResponse({'error': 'Cart item not found'}, status=404)
        
        c.quantity -= 1
        c.save()
        
        user = request.user
        cart = Cart.objects.filter(user=user)
        amount = sum(p.quantity * p.product.discounted_price for p in cart)
        totalamount = amount + 40  # Assuming 40 is a fixed shipping cost

        data = {
            'quantity': c.quantity,
            'amount': amount,
            'totalamount': totalamount
        }    
        
        return JsonResponse(data)

    return JsonResponse({'error': 'Invalid request method'}, status=405)

# def remove_cart(request):
#         if request.method=='GET':
#             prod_id=request.GET['prod_id']
#             c=Cart.objects.get(Q(product=prod_id) & Q(user=request.user))
#             c.delete()
#             user=request.user
#             cart = Cart.objects.filter(user=user)
#             amount=0
#             for p in cart:
#                 value = p.quantity*p.product.discounted_price
#                 amount=amount+value
#             totalamount = amount+40
#             data ={
#                 'amount':amount,
#                 'totalamount':totalamount

#             }    

#             return JsonResponse(data)



# def remove_cart(request):
#     if request.method == 'GET':
#         # Use get() with a default value to avoid KeyError
#         prod_id = request.GET.get('prod_id')
        
#         if not prod_id:
#             return JsonResponse({'error': 'prod_id parameter is missing'}, status=400)
        
#         try:
#             c = Cart.objects.get(Q(product=prod_id) & Q(user=request.user))
#             c.delete()
#         except Cart.DoesNotExist:
#             return JsonResponse({'error': 'Cart item not found'}, status=404)
        
#         user = request.user
#         cart = Cart.objects.filter(user=user)
#         amount = sum(p.quantity * p.product.discounted_price for p in cart)
#         totalamount = amount + 40  # Assuming 40 is a fixed shipping cost

#         data = {
#             'amount': amount,
#             'totalamount': totalamount
#         }    
        
#         return JsonResponse(data)
    
#     return JsonResponse({'error': 'Invalid request method'}, status=405)


# def remove_cart(request):
#     if request.method == 'GET':
#         prod_id = request.GET.get('prod_id')
        
#         if not prod_id:
#             return JsonResponse({'error': 'prod_id parameter is missing'}, status=400)
        
#         try:
#             # Convert prod_id to integer
#             prod_id = int(prod_id)
            
#             # Find and delete all matching cart items
#             carts = Cart.objects.filter(Q(product=prod_id) & Q(user=request.user))
            
#             if not carts.exists():
#                 return JsonResponse({'error': 'Cart item not found'}, status=404)
            
#             carts.delete()
        
#         except ValueError:
#             return JsonResponse({'error': 'Invalid product ID format'}, status=400)
        
#         # Recalculate amounts after deletion
#         user = request.user
#         cart = Cart.objects.filter(user=user)
#         amount = sum(p.quantity * p.product.discounted_price for p in cart)
#         totalamount = amount + 40  # Assuming 40 is a fixed shipping cost

#         data = {
#             'amount': amount,
#             'totalamount': totalamount
#         }
        
#         return JsonResponse(data)
    
#     return JsonResponse({'error': 'Invalid request method'}, status=405)


# def remove_cart(request):
#     if request.method == 'GET':
#         prod_id = request.GET.get('prod_id')
        
#         if not prod_id:
#             return JsonResponse({'error': 'prod_id parameter is missing'}, status=400)
        
#         try:
#             # Convert prod_id to integer
#             prod_id = int(prod_id)
            
#             # Find and delete all matching cart items
#             carts = Cart.objects.filter(Q(product=prod_id) & Q(user=request.user))
            
#             if not carts.exists():
#                 redirect ("/app/cart/")
            
#             carts.delete()
        
#         except ValueError:
#             return JsonResponse({'error': 'Invalid product ID format'}, status=400)
        
#         # Recalculate amounts after deletion
#         user = request.user
#         cart = Cart.objects.filter(user=user)
#         amount = sum(p.quantity * p.product.discounted_price for p in cart)
#         totalamount = amount + 40  # Assuming 40 is a fixed shipping cost

#         data = {
#             'amount': amount,
#             'totalamount': totalamount
#         }
        
#         return JsonResponse(data)
    
#     return JsonResponse({'error': 'Invalid request method'}, status=405)



# def remove_cart(request):
#     if request.method == 'GET':
#         prod_id = request.GET.get('prod_id')
        
#         if not prod_id:

#             redirect('/app/cart/')
        
#         try:
#             # Convert prod_id to integer
#             prod_id = int(prod_id)
            
#             # Find and delete all matching cart items
#             carts = Cart.objects.filter(Q(product=prod_id) & Q(user=request.user))
            
#             if not carts.exists():
#                 return redirect("/app/cart/")  # Redirect if no items found
            
#             carts.delete()
        
#         except ValueError:
#             return JsonResponse({'error': 'Invalid product ID format'}, status=400)
        
#         # Recalculate amounts after deletion
#         user = request.user
#         cart = Cart.objects.filter(user=user)
#         amount = sum(p.quantity * p.product.discounted_price for p in cart)
#         totalamount = amount + 40  # Assuming 40 is a fixed shipping cost

#         data = {
#             'amount': amount,
#             'totalamount': totalamount
#         }
        
#         return JsonResponse(data)
    
#     return JsonResponse({'error': 'Invalid request method'}, status=405)


def remove_cart(request):
    if request.method == 'GET':
        prod_id = request.GET.get('prod_id')
        
        if not prod_id:
            return redirect('/app/cart/')  # Correctly return the redirect response
        
        try:
            # Convert prod_id to integer
            prod_id = int(prod_id)
            
            # Find and delete all matching cart items
            carts = Cart.objects.filter(Q(product=prod_id) & Q(user=request.user))
            
            if not carts.exists():
                return redirect("/app/cart/")  # Redirect if no items found
            
            carts.delete()
        
        except ValueError:
            return JsonResponse({'error': 'Invalid product ID format'}, status=400)
        
        # Recalculate amounts after deletion
        user = request.user
        cart = Cart.objects.filter(user=user)
        amount = sum(p.quantity * p.product.discounted_price for p in cart)
        totalamount = amount + 40  # Assuming 40 is a fixed shipping cost

        data = {
            'amount': amount,
            'totalamount': totalamount
        }
        
        return JsonResponse(data)
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)