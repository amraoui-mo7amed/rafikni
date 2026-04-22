from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.utils.text import slugify
from django.db import transaction
from ..models import Game, GameImage, GameOrder
from dashboard.decorators import admin_required
from ..utils import notify_admins
import json


@login_required
@admin_required
def game_list(request):
    """List all games with filters"""
    query = request.GET.get("q")
    games = Game.objects.all()
    if query:
        games = games.filter(title__icontains=query)
    
    context = {
        "games": games,
        "query": query,
    }
    return render(request, "dashboard/games/list.html", context)


@login_required
@admin_required
def game_create(request):
    """Create a new game with gallery support"""
    if request.method == "POST":
        try:
            with transaction.atomic():
                title = request.POST.get("title")
                price = request.POST.get("price")
                description = request.POST.get("description")
                tags = request.POST.get("tags", "")
                thumbnail = request.FILES.get("thumbnail")
                is_active = request.POST.get("is_active") == "on"
                gallery = request.FILES.getlist("gallery")

                if not title or not price or not thumbnail:
                    return JsonResponse({"success": False, "errors": ["يرجى ملء الحقول الإجبارية."]})

                slug = slugify(title, allow_unicode=True)
                original_slug = slug
                counter = 1
                while Game.objects.filter(slug=slug).exists():
                    slug = f"{original_slug}-{counter}"
                    counter += 1

                game = Game.objects.create(
                    title=title,
                    slug=slug,
                    price=price,
                    description=description,
                    tags=tags,
                    thumbnail=thumbnail,
                    is_active=is_active
                )

                # Save gallery images
                for img in gallery:
                    GameImage.objects.create(game=game, image=img)

                return JsonResponse({
                    "success": True,
                    "message": "تمت إضافة اللعبة بنجاح.",
                    "redirect_url": reverse("dashboard:game_list")
                })
        except Exception as e:
            return JsonResponse({"success": False, "errors": [str(e)]})

    return render(request, "dashboard/games/create.html")


@login_required
@admin_required
def game_edit(request, pk):
    """Edit an existing game"""
    game = get_object_or_404(Game, pk=pk)
    if request.method == "POST":
        try:
            with transaction.atomic():
                game.title = request.POST.get("title")
                game.price = request.POST.get("price")
                game.description = request.POST.get("description")
                game.tags = request.POST.get("tags", "")
                game.is_active = request.POST.get("is_active") == "on"
                
                if request.FILES.get("thumbnail"):
                    game.thumbnail = request.FILES.get("thumbnail")
                
                game.save()

                # Handle gallery additions
                gallery = request.FILES.getlist("gallery")
                for img in gallery:
                    GameImage.objects.create(game=game, image=img)

                return JsonResponse({
                    "success": True,
                    "message": "تم تحديث اللعبة بنجاح.",
                    "redirect_url": reverse("dashboard:game_list")
                })
        except Exception as e:
            return JsonResponse({"success": False, "errors": [str(e)]})

    context = {"game": game}
    return render(request, "dashboard/games/edit.html", context)


@login_required
@admin_required
def game_delete(request, pk):
    """Delete a game"""
    if request.method == "POST":
        try:
            game = get_object_or_404(Game, pk=pk)
            game.delete()
            return JsonResponse({"success": True, "message": "تم حذف اللعبة بنجاح."})
        except Exception as e:
            return JsonResponse({"success": False, "errors": [str(e)]})
    return JsonResponse({"success": False, "errors": ["طلب غير صالح."]})


@login_required
@admin_required
def game_order_list(request):
    """Manage COD orders"""
    orders = GameOrder.objects.all().select_related("game")
    context = {"orders": orders}
    return render(request, "dashboard/games/order_list.html", context)


@login_required
@admin_required
def game_order_status(request, pk):
    """Update order status"""
    order = get_object_or_404(GameOrder, pk=pk)
    if request.method == "POST":
        try:
            status = request.POST.get("status")
            if status in GameOrder.OrderStatus.values:
                order.status = status
                order.save()
                return JsonResponse({"success": True, "message": "تم تحديث حالة الطلب."})
        except Exception as e:
            return JsonResponse({"success": False, "errors": [str(e)]})
    return JsonResponse({"success": False, "errors": ["طلب غير صالح."]})
