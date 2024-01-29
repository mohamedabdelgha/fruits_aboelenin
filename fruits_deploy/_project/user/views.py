from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .models import Supplier, Seller, Container, Item, ContainerItem, Sale, Payment, Lose, ContainerExpense, ContainerBill, SupplierPay
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum
from datetime import datetime
from django.db.models import F
import pytz


#====================================================================================================================
#====================================================================================================================
def register(request):
    pass    
#====================================================================================================================
def login_user(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username = username, password = password)
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.warning(request, 'هناك خطأ في اسم المستخدم او كلمة المرور')

    return render(request, 'login.html')
#====================================================================================================================
def logout_user(request):
    logout(request)
    return render(request, 'logout.html')
#====================================================================================================================
@login_required(login_url="login")
def home(request):
    return render(request, 'home.html')
#====================================================================================================================
#====================================================================================================================
#===========================================CONTAINER===========================================================================
#====================================================================================================================
#====================================================================================================================
@login_required(login_url="login")
def add_container(request):
    if request.method == "POST":
        supplier_name = request.POST.get('supplier')
        date_str = request.POST.get('date')
        type = request.POST.get('type')
        weight = request.POST.get('weight')

        if not supplier_name:
            messages.warning(request, 'يجب إدخال اسم العميل الخاص بالنقلة')
            return redirect('addcontainer')
        try:
            # Try to get the Supplier instance based on the name
            supplier = Supplier.objects.get(name=supplier_name)
        except Supplier.DoesNotExist:
            messages.warning(request, f'العميل ({supplier_name}) غير موجود')
            return redirect('addcontainer')

        if not date_str:
            egypt_tz = pytz.timezone('Africa/Cairo')
            date = timezone.now().astimezone(egypt_tz).date()
        else:
            try:
                date = timezone.datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                messages.warning(request, 'تاريخ غير صالح. يجب أن يكون الشكل YYYY-MM-DD', extra_tags='warning')
                return redirect('addcontainer')

        # Create a new Container instance with the retrieved Supplier
        Container.objects.create(supplier=supplier, date=date, type=type)

        messages.success(request, "تم إضافة نقلة جديدة بنجاح")
        return redirect('addcontainer')
    
    container = Container.objects.all()
    context = {
        'containers':container,
        'supplys': Supplier.objects.all(),
        
        }
    return render(request, 'add.html', context)
#====================================================================================================================
def container_update(request, id):
    container = None 

    if request.method == "POST":
        supplier = request.POST['supplier']
        date_str = request.POST['date']
        type = request.POST['type']

        supplier = supplier.strip()
        type = type.strip()

        try:
            supplier = Supplier.objects.get(name=supplier)
        except Supplier.DoesNotExist:
            messages.warning(request, 'العميل غير موجود')
            return redirect('containerupdate',id=id)

        try:
            if date_str: 
                date = timezone.datetime.strptime(date_str, '%Y-%m-%d').date()
            elif not supplier:
                messages.error(request,"اسم العميل غير موجود")
                return redirect('containerupdate', id=id)
            else:
                egypt_tz = pytz.timezone('Africa/Cairo')
                date = timezone.now().astimezone(egypt_tz).date()


            edit = Container.objects.get(id=id)
            edit.supplier = supplier
            edit.date = date
            edit.type = type
            edit.save()
            messages.success(request, 'تم تعديل بيانات النقلة بنجاح', extra_tags='success')
            return redirect("addcontainer")
        except ValueError:
            messages.warning(request, 'تاريخ غير صالح. يجب أن يكون الشكل YYYY-MM-DD', extra_tags='warning')
            return redirect('containerupdate', id=id)
        except Container.DoesNotExist:
            messages.error(request, 'حدث خطأ، العميل غير موجود', extra_tags='error')
            return redirect("containerupdate")

    else:  # Initial rendering
        try:
            container = Container.objects.get(id=id)  # Retrieve object
        except Container.DoesNotExist:
            messages.error(request, 'حدث خطأ، العميل غير موجود', extra_tags='error')
            return redirect("containerupdate")

    context = {"container": container, "id": id}
    return render(request, 'containerupdate.html', context)
#====================================================================================================================
def container_delete(request,id):
    container_delete = get_object_or_404(Container, id=id )
    if request.method == "POST":
        container_delete.delete()
        return redirect("addcontainer")
    return render(request, 'containerdelete.html')
#====================================================================================================================
@login_required(login_url="login")
def container_details(request, id):
    container = get_object_or_404(Container, pk=id)
    expenses = ContainerExpense.objects.filter(container=container)
    container_bills = ContainerBill.objects.filter(container=container)
    container_items = ContainerItem.objects.filter(container=container)
    sales = Sale.objects.filter(container=container)


    # Fetching total based on container_bills data
    total_of_nakla = sum(bill.total_bill_row for bill in container_bills)

    # Calculate total_bill_price for the same specific container
    total_bill_price = sum(bill.total_bill_row for bill in container_bills)

    context = {
        'container': container,
        'expenses': expenses,
        'container_bills': container_bills,
        'container_items': container_items,
        'total_of_nakla': total_of_nakla,
        'total_bill_price': total_bill_price,
        'sales' : sales,
    }

    if request.method == "POST":
        if 'profits_submit' in request.POST:
            commission = request.POST['commission']
            carry = request.POST['carry']
            tool_rent = request.POST['tool_rent']
            
            commission = 0 if not commission else commission
            carry = 0 if not carry else carry
            tool_rent = 0 if not tool_rent else tool_rent

            edit = Container.objects.get(id=id)
            edit.commission = commission
            edit.carry = carry
            edit.tool_rent = tool_rent
            edit.save()
            messages.success(request, 'تم اضافة خصومات النقلة بنجاح', extra_tags='success')

        elif 'loses_submit' in request.POST:
            expense_amount = request.POST['expense']
            expense_type = request.POST['expense_type']
            expense_notes = request.POST['expense_notes']

            if not expense_amount:
                messages.error(request, 'يجب ادخال المبلغ لاضافة المصروف', extra_tags='error')
            else:
                ContainerExpense.objects.create(
                    container=container,
                    expense=expense_amount,
                    expense_type=expense_type,
                    expense_notes=expense_notes,
                )
                messages.success(request, 'تمت اضافة المصروف بنجاح', extra_tags='success')

        elif 'add_bill_submit' in request.POST:
            count = request.POST['count']
            weight = request.POST['weight']
            price = request.POST['price']
            container_item_id = request.POST['container_item']

            if not (count and weight and price and container_item_id):
                messages.error(request, 'برجاء ادخال كافة البيانات', extra_tags='error')
            else:
                container_item = get_object_or_404(ContainerItem, pk=container_item_id)

                ContainerBill.objects.create(
                    container=container,
                    container_item=container_item,
                    count=count,
                    weight=weight,
                    price=price,
                )

                messages.success(request, 'تم ادخال خانة فاتورة نقلة', extra_tags='success')

        return redirect("condetails", id=id)

    return render(request, 'cardetails.html', context)
#====================================================================================================================
def container_bill_update(request, id):
    container_bill = get_object_or_404(ContainerBill, id=id)
    container_items = ContainerItem.objects.all()  # You may need to filter this based on your requirements

    if request.method == 'POST':
        count = request.POST.get('count')
        weight = request.POST.get('weight')
        price = request.POST.get('price')
        container_item_id = request.POST.get('container_item')

        if not (count and weight and price and container_item_id):
            pass

        container_item = get_object_or_404(ContainerItem, pk=container_item_id)
        container_bill.count = count
        container_bill.weight = weight
        container_bill.price = price
        container_bill.container_item = container_item
        container_bill.save()

        return redirect('condetails', id=container_bill.container.id)

    context = {
        'container_bill': container_bill,
        'container_items': container_items,
    }
    return render(request, 'containerbillupdate.html', context)
#====================================================================================================================
def container_bill_delete(request, id):
    container_bill = get_object_or_404(ContainerBill, id=id)
    if request.method == "POST":
        container_bill.delete()
        return redirect("condetails", id=container_bill.container.id)
    return render(request, 'containerbilldelete.html')
#====================================================================================================================
def container_expenses_delete(request,id):
    containerexpensesdelete = get_object_or_404(ContainerExpense, id=id )
    if request.method == "POST":
        containerexpensesdelete.delete()
        return redirect("condetails", id=containerexpensesdelete.container.id)
    return render(request, 'containerexpensesdelete.html')
#====================================================================================================================
def container_items(request, id):
    container = get_object_or_404(Container, pk=id)
    items = Item.objects.all()
    context = {
        'container': container,
        'items' : items
    }
    if request.method == 'POST':
        form_data = request.POST

        try:
            item_name = form_data['item_name']
            count = float(form_data['count'])
            tool = form_data['tool']
            price = float(form_data['price'])
            weight = float(form_data['weight'])  

            item_name = item_name.strip()

            if not price:
                raise ValueError("الرجاء إدخال السعر")
            if not count:
                raise ValueError("الرجاء إدخال العدد")
            if count <= 0 or price <= 0 or weight < 0:  # Check for valid weight
                raise ValueError("العدد والسعر والوزن يجب أن يكونا أكبر من صفر")

            item = Item.objects.get(name=item_name)
        except ValueError as e:
            messages.error(request, str(e))
        except Item.DoesNotExist:
            messages.error(request, f"الصنف {item_name} غير موجود")
        else:
            # Check if a similar ContainerItem with the same item_name already exists in the container
            existing_item = ContainerItem.objects.filter(
                container=container,
                item__name=item_name,
            ).first()

            if existing_item:
                messages.warning(request, f"الصنف ({item_name}) موجود بالفعل في النقلة ")
            else:
                ContainerItem.objects.create(
                    container=container,
                    item=item,
                    count=count,
                    tool=tool,
                    price=price,
                    item_weight=weight  
                )
                messages.success(request, "تم إضافة الصنف بنجاح")
                return redirect('containeritems', id)

    return render(request, 'containerItems.html',context)
#====================================================================================================================
def containeritem_delete(request, id):
    container_item_delete = get_object_or_404(ContainerItem, id=id)

    # Check if the ContainerItem is involved in any sale operation
    if Sale.objects.filter(container_item=container_item_delete).exists():
        messages.warning(request, "هذا الصنف تم ادراجه في عملية بيع ,الحذف قد يسبب مشاكل تقنية")
        return redirect("containeritems", id=container_item_delete.container.id)

    if request.method == "POST":
        if Sale.objects.filter(container_item=container_item_delete).exists():
            messages.error(request, "هذا الصنف تم ادراجه في عملية بيع ,الحذف قد يسبب مشاكل تقنية")
        else:
            container_item_delete.delete()
            return redirect("containeritems", id=container_item_delete.container.id)

    return render(request, 'containeritemdelete.html', {'container': container_item_delete.container})
#====================================================================================================================
@login_required(login_url="login")
def today_containers(request):
    egypt_tz = pytz.timezone('Africa/Cairo')
    todays_date = timezone.now().astimezone(egypt_tz).date() 
    containers = Container.objects.filter(date=todays_date) 
    context = {'container': containers} 

    return render(request, 'today.html', context)
#====================================================================================================================
@login_required(login_url="login")
def remain_containers(request):
    all_containers = Container.objects.all()
    remain_containers = [container for container in all_containers if container.total_remaining_count > 0]

    context = {
        'containers': remain_containers,
    }
    return render(request, 'remain.html', context)
#====================================================================================================================
@login_required(login_url="login")
def finished_containers(request):
    all_containers = Container.objects.all()
    finished_containers = [container for container in all_containers if container.total_remaining_count == 0]
    
    context = {
        'containers': finished_containers,
    }
    return render(request, 'finished.html', context)
#====================================================================================================================
@login_required(login_url="login")
def sell_container(request, id):
    container = get_object_or_404(Container, pk=id)
    sales = Sale.objects.filter(container=container)
    sellers = Seller.objects.all()

    context = {
        'container': container,
        'sales': sales,
        'sellers': sellers,
    }

    if request.method == 'POST':
        seller_name = request.POST.get('seller')
        weight = request.POST.get('weight')
        count = request.POST.get('count')
        price = request.POST.get('price')
        tool = request.POST.get('tool')
        container_item_name = request.POST.get('container_item')
        date_str = request.POST.get('date')

        # price = float(price)
        seller_name = seller_name.strip()
        container_item_name = container_item_name.strip()

        if not seller_name or not weight or not count or not price or not tool or not container_item_name:
            messages.warning(request, "تأكد من أن جميع الخانات ممتلئة ببيانات صحيحة")
            return redirect('sellcon', id=id)
        if float(weight) < 0 or float(price) < 0:
            messages.warning(request, "السعر والوزن لا يجب أن يكونا أصغر من الصفر")
            return redirect('sellcon', id=id)

        if int(count) <= 0 or float(weight) <=0 or float(price) <=0  :
            messages.warning(request, "لا يمكن ان يكون العدد أو الوزن او السعر يساوي صفر ")
            return redirect('sellcon', id=id)
        
        if not container_item_name:
            messages.warning(request, "ادخل اسم الصنف")
            return redirect('sellcon', pk=id)

        try:
            seller = Seller.objects.get(name=seller_name)
        except Seller.DoesNotExist:
            messages.warning(request, "اسم البائع غير موجود")
            return redirect('sellcon', id=id)

        try:
            container_item = ContainerItem.objects.get(container=container, item__name=container_item_name)

            if int(count) > container_item.remaining_count:
                messages.error(request, f"الكمية المدخلة ({count}) أكبر من الكمية المتبقية في الصنف و التي هي : ({container_item.remaining_count})")
                return redirect('sellcon', id=id)
        except ContainerItem.DoesNotExist:
            messages.warning(request, "اسم الصنف غير موجود")
            return redirect('sellcon', id=id)

        if not date_str:
            egypt_tz = pytz.timezone('Africa/Cairo')
            date = timezone.now().astimezone(egypt_tz).date()
        else:
            try:
                date = timezone.datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                messages.warning(request, 'تاريخ غير صالح. يجب أن يكون الشكل YYYY-MM-DD', extra_tags='warning')
                return redirect('sellcon', pk=id)

        Sale.objects.create(
            seller=seller,
            container=container,
            date=date,
            weight=weight,
            count=count,
            price=price,
            container_item=container_item,
            tool=tool
        )

        messages.success(request, "تمت إضافة عملية بيع بنجاح")
        return redirect('sellcon', id=id)


    return render(request, 'sellcar.html', context)
#====================================================================================================================
# def sale_update(request, id):
#     sale = get_object_or_404(Sale, id=id)
#     container_id = sale.container.id
#     sellers = Seller.objects.all()

#     context = {
#         'sale': sale,
#         'id': sale.id,
#         'sellers': sellers,
#     }

#     if request.method == "POST":
#         weight = request.POST['weight']
#         count = request.POST['count']
#         price = request.POST['price']
#         seller_name = request.POST['seller']
#         tool = request.POST['tool']
#         date_str = request.POST['date']
#         container_item_name = request.POST['container_item']

#         if not seller_name or not weight or not count or not price or not tool or not container_item_name:
#             messages.warning(request, "تأكد من أن جميع الخانات ممتلئة ببيانات صحيحة")
#             return redirect('sellcon', id=id)
#         if float(weight) < 0 or float(price) < 0:
#             messages.warning(request, "السعر والوزن لا يجب أن يكونا أصغر من الصفر")
#             return redirect('sellcon', id=container_id)

#         if not container_item_name:
#             messages.warning(request, "ادخل اسم الصنف")
#             return redirect('sellcon', id=container_id)

#         try:
#             # Fetch the Seller instance corresponding to the given name
#             seller = Seller.objects.get(name=seller_name)
#         except Seller.DoesNotExist:
#             messages.warning(request, "اسم البائع الذي ادخلته في التعديل غير صحيح")
#             return redirect("sellcon", id=container_id)

#         try:
#             # Fetch the ContainerItem instance corresponding to the given name
#             container_item = ContainerItem.objects.get(container=sale.container, item__name=container_item_name)
#         except ContainerItem.DoesNotExist:
#             messages.warning(request, "اسم الصنف الذي ادخلته في عملية التعديل غير صحيح")
#             return redirect("sellcon", id=container_id)

#         if not date_str:
#             date = timezone.now().date()
#         else:
#             try:
#                 date = timezone.datetime.strptime(date_str, '%Y-%m-%d').date()
#             except ValueError:
#                 messages.warning(request, 'تاريخ غير صالح. يجب أن يكون الشكل YYYY-MM-DD', extra_tags='warning')
#                 return redirect('sellcon', id=container_id)

#         # Increment the remaining_count of the old associated ContainerItem
#         if sale.container_item:
#             sale.container_item.remaining_count = F('remaining_count') + sale.count
#             sale.container_item.save()

#         # Update the Sale instance
#         sale.weight = weight
#         sale.count = count
#         sale.price = price
#         sale.seller = seller
#         sale.tool = tool
#         sale.date = date
#         sale.container_item = container_item
#         sale.save()

#         # Decrement the remaining_count of the new associated ContainerItem
#         if sale.container_item:     
#             sale.container_item.remaining_count = F('remaining_count') - sale.count
#             sale.container_item.save()

#         messages.success(request, "تم التعديل بنجاح")
#         return redirect("sellcon", id=container_id)

#     return render(request, 'saleupdate.html', context)
#====================================================================================================================
def sale_delete(request, id):
    sale_to_delete = get_object_or_404(Sale, id=id)
    container_id = sale_to_delete.container.id  

    if request.method == "POST":
        # Retrieve the associated ContainerItem
        container_item = sale_to_delete.container_item

        if container_item:
            container_item.remaining_count = F('remaining_count') + sale_to_delete.count
            container_item.save()

        sale_to_delete.delete()
        return redirect("sellcon", id=container_id) 

    context = {
        'sale': sale_to_delete,  
    }
    return render(request, "saledelete.html", context)
#====================================================================================================================
#====================================================================================================================
#==============================================calculations=========================================================
#====================================================================================================================
#====================================================================================================================
@login_required(login_url="login")
def loses(request):
    loses = Lose.objects.all()
    context = {'loses': loses}

    if request.method == 'POST':
        amount = request.POST.get('amount')
        lose_type = request.POST.get('lose_type')
        date = request.POST.get('date')

        if int(amount) < 0:
            messages.error(request, "قيمة المصروف أقل من صفر")
            return redirect('loses')

        egypt_tz = pytz.timezone('Africa/Cairo')
        lose_instance = Lose(
            amount=amount,
            lose_type=lose_type,
            date=date if date else timezone.now().astimezone(egypt_tz).date(),
        )
        lose_instance.save()
        return redirect('loses')

    return render(request, 'loses.html', context)
#====================================================================================================================
def loses_delete(request, id):
    loses_delete = get_object_or_404(Lose, id=id )
    if request.method == "POST":
        loses_delete.delete()
        return redirect("loses")
    return render(request,"losesdelete.html")
#====================================================================================================================
@login_required(login_url="login")
def profits(request):
    payments = Payment.objects.all()
    sel = Seller.objects.all()
    context = {
        'payments': payments,
        'sels': sel,
    }

    if request.method == "POST":
        seller_name = request.POST.get('seller')
        paid_money = request.POST.get('paid')
        forgive = request.POST.get('forgive')
        date_str = request.POST.get('date')

        if not seller_name:
            messages.warning(request, 'يجب إدخال اسم البائع')
            return redirect("profits")

        if not forgive:
            forgive = 0

        try:
            seller = Seller.objects.get(name=seller_name)
        except Seller.DoesNotExist:
            messages.warning(request, "اسم البائع غير موجود")
            return redirect("profits")

        if not paid_money:
            messages.warning(request, 'برجاء إدخال المبلغ')
            return redirect("profits")

        egypt_tz = pytz.timezone('Africa/Cairo')

        if not date_str:
            date = timezone.now().astimezone(egypt_tz).date()
        else:
            try:
                date = timezone.datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                messages.warning(request, 'تاريخ غير صالح. يجب أن يكون الشكل YYYY-MM-DD', extra_tags='warning')
                return redirect("profits")

        payment = Payment(
            seller=seller,
            paid_money=paid_money,
            forgive=forgive,
            date=date,
        )
        payment.save()
        payment.temp_rest = payment.rest
        payment.save()
        messages.success(request, 'تم إضافة عملية دفع جديدة بنجاح', extra_tags='success')
        return redirect("profits")

    return render(request, 'profits.html', context)
#====================================================================================================================
def profits_update(request, id):
    payment = Payment.objects.get(id=id)

    if request.method == "POST":
        paid_money = request.POST['paid_money']
        forgive = request.POST['forgive']
        date_str = request.POST['date']

        try:
            if date_str:
                date = timezone.datetime.strptime(date_str, '%Y-%m-%d').date()
            elif not paid_money:
                messages.error(request, "ادخل المبلغ")
                return redirect('profitsupdate', id=id)
            elif not forgive:
                messages.error(request, "اذا كانت قيمة السماح تساوي صفر , يرجى ادخال قيمة 0")
                return redirect('profitsupdate', id=id)
            else:
                egypt_tz = pytz.timezone('Africa/Cairo')
                date = timezone.now().astimezone(egypt_tz).date()

            edit = Payment.objects.get(id=id)
            edit.paid_money = paid_money
            edit.forgive = forgive
            edit.date = date
            edit.save()
            edit.temp_rest = edit.rest
            edit.save()
            messages.success(request, "تم تعديل عملية البيع بنجاح")
            return redirect("profits")
        except ValueError:
            messages.warning(request, 'تاريخ غير صالح. يجب أن يكون الشكل YYYY-MM-DD', extra_tags='warning')
            return redirect('profitsupdate', id=id)

    context = {'payment': payment}
    return render(request, 'profitsupdate.html', context)
#====================================================================================================================
def profits_delete(request, id):
    profits_delete = get_object_or_404(Payment, id=id )
    if request.method == "POST":
        profits_delete.delete()
        return redirect("profits")
    return render(request, 'profitsdelete.html')
#====================================================================================================================
@login_required(login_url="login")
def day_money(request):
    if request.method == 'POST':
        date_str = request.POST.get('date')
        selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()

        egypt_tz = pytz.timezone('Africa/Cairo')
        selected_date = egypt_tz.localize(datetime.combine(selected_date, datetime.min.time())).date()

        total_payments = Payment.objects.filter(date__date=selected_date).aggregate(Sum('paid_money'))['paid_money__sum']
        total_payments = total_payments or 0  

        total_loses = Lose.objects.filter(date=selected_date).aggregate(Sum('amount'))['amount__sum']
        total_loses = total_loses or 0  

        remaining_amount = total_payments - total_loses

        return render(request, 'daymoney.html', {
            'total_payments': total_payments,
            'total_loses': total_loses,
            'remaining_amount': remaining_amount,
        })

    return render(request, 'daymoney.html', {'total_payments': None})
#====================================================================================================================
#====================================================================================================================
#=============================================ITEMS==================================================================
#====================================================================================================================
#====================================================================================================================
@login_required(login_url="login")
def add_items(request):
    if request.method == "POST":
        name = request.POST.get('name')
        date_str = request.POST.get('date')

        name = name.strip()

        if not name:
            messages.warning(request, 'يجب إدخال اسم الصنف')
            return redirect('items')

        elif not date_str:
            egypt_tz = pytz.timezone('Africa/Cairo')
            date = timezone.now().astimezone(egypt_tz).date()
        else:
            try:
                date = timezone.datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                messages.warning(request, 'تاريخ غير صالح. يجب أن يكون الشكل YYYY-MM-DD', extra_tags='warning')
                return redirect('items')

        # Check if an item with the same name already exists
        existing_item = Item.objects.filter(name=name).first()

        if existing_item:
            messages.warning(request, f"الصنف '{name}' موجود بالفعل في قاعدة البيانات")
        else:
            Item.objects.create(name=name, date=date)
            messages.success(request, "تم إضافة صنف جديد بنجاح")
            return redirect('items')

    items = Item.objects.all()
    context = {'items': items}

    return render(request, "kinds.html", context)
#====================================================================================================================
def item_update(request, id):
    item = None

    if request.method == "POST":
        name = request.POST.get('name')
        date_str = request.POST.get('date')

        name = name.strip()

        try:
            if date_str:
                date = timezone.datetime.strptime(date_str, '%Y-%m-%d').date()
            elif not name:
                messages.error(request, "اسم الصنف غير موجود")
                return redirect('itemupdate', id=id)
            else:
                egypt_tz = pytz.timezone('Africa/Cairo')
                date = timezone.now().astimezone(egypt_tz).date()

            edit = Item.objects.get(id=id)
            edit.name = name
            edit.date = date
            edit.save()
            messages.success(request, 'تم تعديل بيانات الصنف بنجاح', extra_tags='success')
            return redirect("items")
        except ValueError:
            messages.warning(request, 'تاريخ غير صالح. يجب أن يكون الشكل YYYY-MM-DD', extra_tags='warning')
            return redirect('itemupdate', id=id)
        except Item.DoesNotExist:
            messages.error(request, 'حدث خطأ، الصنف غير موجود', extra_tags='error')
            return redirect("itemupdate", id=id)

    else: 
        try:
            item = Item.objects.get(id=id)
        except Item.DoesNotExist:
            messages.error(request, 'حدث خطأ، الصنف غير موجود', extra_tags='error')
            return redirect("itemupdate", id=id)

    context = {"item": item, "id": id}
    return render(request, 'kindsupdate.html', context)
#====================================================================================================================
def item_delete(request,id):
    item_delete = get_object_or_404(Item, id=id )
    if request.method == "POST":
        item_delete.delete()
        return redirect("items")
    return render(request, 'kindsdelete.html')
#====================================================================================================================
#====================================================================================================================
#===========================================SELLER & SUPPLIER=========================================================================
#====================================================================================================================
#====================================================================================================================
@login_required(login_url="login")
def seller_accounts(request):
    seller = Seller.objects.all()
    context = {'seller': seller}

    if request.method == "POST":
        name = request.POST.get('name')
        place = request.POST.get('place', 'غير محدد')  
        date_str = request.POST.get('date')
        seller_opening_balance = request.POST.get('seller_opening_balance')

        name = name.strip()
        place = place.strip()

        if not name:
            messages.warning(request, 'يجب إدخال اسم البائع')
            return redirect('selleraccounts')
        if not place:
            messages.warning(request, 'برجاء إدخال اسم المنطقة')
            return redirect('selleraccounts')
        if not seller_opening_balance:
            seller_opening_balance = 0

        if Seller.objects.filter(name=name).exists():
            messages.warning(request, f'اسم البائع ({name}) موجود بالفعل في قاعدة البيانات')
            return redirect('selleraccounts')

        if not date_str:
            egypt_tz = pytz.timezone('Africa/Cairo')
            date = timezone.now().astimezone(egypt_tz).date()
        else:
            try:
                date = timezone.datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                messages.warning(request, 'تاريخ غير صالح. يجب أن يكون الشكل YYYY-MM-DD', extra_tags='warning')
                return redirect('selleraccounts')

        if Seller.objects.create(name=name, place=place, date=date,seller_opening_balance=seller_opening_balance):
            messages.success(request, 'تم إضافة بائع جديد بنجاح', extra_tags='success')
            return redirect('selleraccounts')
        else:
            messages.warning(request, 'حدث خطأ، يرجى التأكد من أن جميع البيانات صحيحة', extra_tags='error')

    return render(request, 'sellersaccounts.html', context)
#====================================================================================================================
@login_required(login_url="login")
def seller_page(request, id):
    seller = get_object_or_404(Seller, id=id)
    payments = Payment.objects.filter(seller=seller).order_by('-date')
    sales = Sale.objects.filter(seller=seller).order_by('-date')
    sales_by_date = Sale.objects.filter(seller=seller).values('date').annotate(
        total_meal=Sum('total_sell_price')
    )
    context = {
        'seller': seller,
        'payments': payments,
        'sales': sales,
        'sales_by_date': sales_by_date, 
    }

    if request.method == "POST":
        seller_name = request.POST.get('seller')  
        paid_money = request.POST.get('paid')
        forgive = request.POST.get('forgive')
        date_str = request.POST.get('date')

        if not seller_name:
            messages.warning(request, 'يجب إدخال اسم البائع')
            return redirect('sellerpage', id=id)

        if not forgive:
            forgive = 0

        try:
            seller = Seller.objects.get(name=seller_name)
        except Seller.DoesNotExist:
            messages.warning(request, "اسم البائع غير موجود")
            return redirect('sellerpage', id=id)

        if not paid_money:
            messages.warning(request, 'برجاء إدخال المبلغ')
            return redirect('sellerpage', id=id)

        if not date_str:
            egypt_tz = pytz.timezone('Africa/Cairo')
            date = timezone.now().astimezone(egypt_tz).date()
        else:
            try:
                date = timezone.datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                messages.warning(request, 'تاريخ غير صالح. يجب أن يكون الشكل YYYY-MM-DD', extra_tags='warning')
                return redirect('sellerpage', pk=id)
            
        payment = Payment(
            seller=seller,
            paid_money=paid_money,
            forgive=forgive,
            date=date,
        )
        payment.save()

        # Update temp_rest to the new value of rest after saving
        payment.temp_rest = payment.rest
        payment.save()
        messages.success(request, 'تم إضافة عملية دفع جديدة بنجاح', extra_tags='success')
        return redirect('sellerpage', id=id)

    return render(request, 'sellerpage.html', context)
#====================================================================================================================
def seller_update(request, id):
    seller = None  # Initialize

    if request.method == "POST":
        name = request.POST['name']
        place = request.POST['place']
        date_str = request.POST['date']
        seller_opening_balance = request.POST['seller_opening_balance']

        name = name.strip()
        place = place.strip()

        try:
            if date_str:  
                date = timezone.datetime.strptime(date_str, '%Y-%m-%d').date()
            elif not name:
                messages.error(request, "اسم البائع غير موجود")
                return redirect('sellerupdate', id=id)
            elif not seller_opening_balance:
                messages.error(request, "اذا كان الرصيد الافتتاحي يساوي صفر , يرجى ادخال صفر")
                return redirect('sellerupdate', id=id)
            elif not place:
                messages.error(request, "يرجى إدخال المنطقة")
                return redirect('sellerupdate', id=id)
            else:
                egypt_tz = pytz.timezone('Africa/Cairo')
                date = timezone.now().astimezone(egypt_tz).date()

            edit = Seller.objects.get(id=id)
            edit.name = name
            edit.place = place
            edit.seller_opening_balance = seller_opening_balance
            edit.date = date
            edit.save()
            messages.success(request, 'تم تعديل بيانات البائع بنجاح', extra_tags='success')
            return redirect("selleraccounts")
        except ValueError:
            messages.warning(request, 'تاريخ غير صالح. يجب أن يكون الشكل YYYY-MM-DD', extra_tags='warning')
            return redirect('sellerupdate', id=id)
        except Seller.DoesNotExist:
            messages.error(request, 'حدث خطأ، العميل غير موجود', extra_tags='error')
            return redirect("selleraccounts")

    else: 
        try:
            seller = Seller.objects.get(id=id)  
        except Seller.DoesNotExist:
            messages.error(request, 'حدث خطأ، العميل غير موجود', extra_tags='error')
            return redirect("selleraccounts")

    context = {"seller": seller, "id": id}
    return render(request, 'sellerupdate.html', context)
#====================================================================================================================
def seller_delete(request,id):
    seller_delete = get_object_or_404(Seller, id=id )
    if request.method == "POST":
        seller_delete.delete()
        return redirect("selleraccounts")
    return render(request, "sellerdelete.html")
#====================================================================================================================
@login_required(login_url="login")
def seller_sort(request):
    seller = Seller.objects.all()
    context = {'seller':seller}
    return render(request, 'sellersort.html', context)
#====================================================================================================================
@login_required(login_url="login")
def suppliers_accounts(request):
    sup = Supplier.objects.all()
    context = {'sup': sup}

    if request.method == "POST":
        name = request.POST.get('name')
        place = request.POST.get('place', 'غير محدد')  
        date_str = request.POST.get('date')
        opening_balance = request.POST.get('opening_balance')
        

        name = name.strip()
        place = place.strip()

        if not name:
            messages.warning(request, 'يجب إدخال اسم العميل')
            return redirect('suppliersaccounts')
        if not place:
            messages.warning(request, 'برجاء إدخال اسم المنطقة')
            return redirect('suppliersaccounts')
        if not opening_balance:
            opening_balance = 0

        if Supplier.objects.filter(name=name).exists():
            messages.warning(request, f'اسم العميل ({name}) موجود بالفعل في قاعدة البيانات')
            return redirect('suppliersaccounts')

        if not date_str:
            egypt_tz = pytz.timezone('Africa/Cairo')
            date = timezone.now().astimezone(egypt_tz).date()
        else:
            try:
                date = timezone.datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                messages.warning(request, 'تاريخ غير صالح. يجب أن يكون الشكل YYYY-MM-DD', extra_tags='warning')
                return redirect('suppliersaccounts')

        if Supplier.objects.create(name=name, place=place, date=date, opening_balance=opening_balance):
            messages.success(request, 'تم إضافة عميل جديد بنجاح', extra_tags='success')
            return redirect('suppliersaccounts')
        else:
            messages.warning(request, 'حدث خطأ، يرجى التأكد من أن جميع البيانات صحيحة', extra_tags='error')
            return redirect('suppliersaccounts')

    return render(request, 'suppliersaccounts.html', context)
#====================================================================================================================\
@login_required(login_url="login")
def supplier_sort(request):
    sup = Supplier.objects.all()
    context = {'sup': sup}
    return render(request,'suppliersort.html',context)
#====================================================================================================================
@login_required(login_url="login")
def supplier_page(request, id):
    sup = get_object_or_404(Supplier, id=id)
    containers = sup.container_set.all()
    context = {'sup': sup, 'containers': containers}
    return render(request, 'supplierpage2.html', context)
#====================================================================================================================
@login_required(login_url="login")
def supplier_update(request, id):
    sup = None  # Initialize sup

    if request.method == "POST":
        name = request.POST['name']
        place = request.POST['place']
        opening_balance = request.POST['opening_balance']
        date_str = request.POST['date']

        name = name.strip()
        place = place.strip()

        try:
            if date_str: 
                date = timezone.datetime.strptime(date_str, '%Y-%m-%d').date()
            elif not opening_balance:
                messages.error(request, "اذا كان الرصيد الافتتاحي يساوي صفر فيرجى ادخال صفر")
                return redirect('supplierupdate', id=id)
            elif not name:
                messages.error(request, "اسم العميل غير موجود")
                return redirect('supplierupdate', id=id)
            elif not place:
                messages.error(request, "يرجى إدخال المنطقة")
                return redirect('supplierupdate', id=id)
            else:
                egypt_tz = pytz.timezone('Africa/Cairo')
                date = timezone.now().astimezone(egypt_tz).date()

            edit = Supplier.objects.get(id=id)
            edit.name = name
            edit.place = place
            edit.opening_balance = opening_balance
            edit.date = date
            edit.save()
            messages.success(request, 'تم تعديل بيانات العميل بنجاح', extra_tags='success')
            return redirect("suppliersaccounts")
        except ValueError:
            messages.warning(request, 'تاريخ غير صالح. يجب أن يكون الشكل YYYY-MM-DD', extra_tags='warning')
            return redirect('supplierupdate', id=id)
        except Supplier.DoesNotExist:
            messages.error(request, 'حدث خطأ، العميل غير موجود', extra_tags='error')
            return redirect("suppliersaccounts")

    else: 
        try:
            sup = Supplier.objects.get(id=id)
        except Supplier.DoesNotExist:
            messages.error(request, 'حدث خطأ، العميل غير موجود', extra_tags='error')
            return redirect("suppliersaccounts")

    context = {"sup": sup, "id": id}
    return render(request, 'supplierupdate.html', context)
#====================================================================================================================
def supplier_delete(request,id):
    supplier_delete = get_object_or_404(Supplier, id=id )
    if request.method == "POST":
        supplier_delete.delete()
        return redirect("suppliersaccounts")
    return render(request, 'suppliersdelete.html')
#====================================================================================================================
def supplier_profits(request):
    sup = Supplier.objects.all()
    pay = SupplierPay.objects.all()
    context = {
        'sup': sup,
        'pay':pay,
        }

    if request.method == "POST":
        supplier_name = request.POST.get('supplier')
        pay = request.POST.get('pay')  
        date_str = request.POST.get('date')
    
        supplier_name = supplier_name.strip()

        if not supplier_name:
            messages.warning(request, 'يجب إدخال اسم العميل')
            return redirect('supplierprofits')
        if not pay:
            messages.warning(request, 'برجاء إدخال المبلغ')
            return redirect('supplierprofits')
        if not date_str:
            egypt_tz = pytz.timezone('Africa/Cairo')
            date = timezone.now().astimezone(egypt_tz).date()
        else:
            try:
                date = timezone.datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                messages.warning(request, 'تاريخ غير صالح. يجب أن يكون الشكل YYYY-MM-DD', extra_tags='warning')
                return redirect('supplierprofits')

        try:
            supplier = Supplier.objects.get(name=supplier_name)
        except Supplier.DoesNotExist:
            messages.warning(request, 'اسم العميل غير موجود')
            return redirect('supplierprofits')

        SupplierPay.objects.create(supplier=supplier, pay=pay, date=date)
        messages.success(request, 'تم إضافة صرف نقدية بنجاح', extra_tags='success')
        return redirect('supplierprofits')

    return render(request, 'supplierprofits.html', context)
#====================================================================================================================
def supplier_profits_delete(request, id):
    supplier_profits_delete = get_object_or_404(SupplierPay, id=id )
    if request.method == "POST":
        supplier_profits_delete.delete()
        return redirect("suppliersaccounts")
    return render(request, "supplierprofitsdelete.html")
#====================================================================================================================
def recent_actions(request):
    return render(request, 'reports.html')
#====================================================================================================================