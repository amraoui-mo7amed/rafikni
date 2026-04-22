from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.http import JsonResponse
from django.db import transaction
from dashboard.models import Game, GameOrder
from dashboard.utils import get_algeria_wilayas, get_algeria_communes, notify_admins


def game_list(request):
    """Public gallery of active games"""
    games = Game.objects.filter(is_active=True)
    return render(request, "games/list.html", {"games": games})


def game_detail(request, slug):
    """Product page with order form"""
    game = get_object_or_404(Game, slug=slug, is_active=True)
    wilayas = get_algeria_wilayas()
    
    context = {
        "game": game,
        "wilayas": wilayas,
    }
    return render(request, "games/detail.html", context)


def get_communes_ajax(request):
    """Helper to load communes for a wilaya"""
    wilaya_code = request.GET.get("wilaya_code")
    if wilaya_code:
        communes = get_algeria_communes(wilaya_code)
        return JsonResponse({"success": True, "data": communes})
    return JsonResponse({"success": False, "errors": ["رمز الولاية مفقود"]})


def place_order(request):
    """Process anonymous COD order"""
    if request.method == "POST":
        try:
            with transaction.atomic():
                game_id = request.POST.get("game_id")
                full_name = request.POST.get("full_name")
                phone_number = request.POST.get("phone_number")
                wilaya = request.POST.get("wilaya")
                commune = request.POST.get("commune")
                address = request.POST.get("address")

                if not all([game_id, full_name, phone_number, wilaya, commune, address]):
                    return JsonResponse({"success": False, "errors": ["يرجى ملء جميع معلومات التوصيل."]})

                game = get_object_or_404(Game, id=game_id)
                
                order = GameOrder.objects.create(
                    game=game,
                    full_name=full_name,
                    phone_number=phone_number,
                    wilaya=wilaya,
                    commune=commune,
                    address=address,
                    user=request.user if request.user.is_authenticated else None
                )

                # Notify admins
                notify_admins(
                    title="طلب جديد للعبة",
                    message=f"هناك طلب جديد للعبة {game.title} من الزبون {full_name}.",
                    notification_type="info",
                    link=reverse("dashboard:game_order_list")
                )

                return JsonResponse({
                    "success": True,
                    "message": "تم استلام طلبك بنجاح! سنتصل بك قريباً لتأكيد التوصيل."
                })
        except Exception as e:
            return JsonResponse({"success": False, "errors": [str(e)]})
    
    return JsonResponse({"success": False, "errors": ["طلب غير صالح."]})
