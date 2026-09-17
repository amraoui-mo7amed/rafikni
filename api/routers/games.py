"""
Educational Games & COD Store Router for Rafikni Platform.
Endpoints for public store catalog, gallery viewing, Cash on Delivery (COD) checkout, and order status updates.
"""

from typing import List, Optional
from ninja import Router, Form, File, UploadedFile
from django.utils.text import slugify
from django.db import transaction
from django.urls import reverse

from dashboard.models import Game, GameImage, GameOrder
from dashboard.utils import notify_admins
from api.security import AdminAuth
from api.utils import api_response
from api.serializers import serialize_game, serialize_game_order
from api.schemas.common import ApiResponseSchema
from api.schemas.games import (
    GameCardSchema,
    GameDetailSchema,
    PlaceOrderSchema,
    GameOrderSchema,
    UpdateOrderStatusSchema,
)

router = Router()


@router.get("/", response=ApiResponseSchema[List[GameCardSchema]])
def list_games(request):
    """
    Public catalog of active educational and sensory games.
    """
    games = Game.objects.filter(is_active=True).order_by("-created_at")
    items = [serialize_game(g, request) for g in games]
    return api_response(success=True, message="تم جلب الألعاب بنجاح", data=items, status=200)


@router.post("/orders", response={201: ApiResponseSchema[GameOrderSchema], 400: ApiResponseSchema[None], 404: ApiResponseSchema[None]})
def place_cod_order(request, data: PlaceOrderSchema):
    """
    Place a Cash on Delivery (COD) order. Open to guests and authenticated users.
    Validates delivery fields and dispatches real-time alert to platform administrators.
    """
    if not all([data.game_id, data.full_name, data.phone_number, data.wilaya, data.commune, data.address]):
        return api_response(
            success=False,
            message="يرجى ملء جميع معلومات التوصيل المطلوبة",
            errors=["يرجى ملء جميع معلومات التوصيل المطلوبة"],
            status=400,
        )

    try:
        game = Game.objects.get(id=data.game_id, is_active=True)
    except Game.DoesNotExist:
        return api_response(success=False, message="اللعبة غير متوفرة حالياً", errors=["اللعبة غير متوفرة"], status=404)

    try:
        with transaction.atomic():
            order = GameOrder.objects.create(
                game=game,
                full_name=data.full_name,
                phone_number=data.phone_number,
                wilaya=data.wilaya,
                commune=data.commune,
                address=data.address,
                user=request.user if request.user.is_authenticated else None,
            )

        notify_admins(
            title="طلب جديد للعبة",
            message=f"هناك طلب جديد للعبة {game.title} من الزبون {data.full_name}.",
            notification_type="info",
            link=reverse("dashboard:game_order_list"),
        )

        order_data = serialize_game_order(order)
        return api_response(
            success=True,
            message="تم استلام طلبك بنجاح! سنتصل بك قريباً لتأكيد التوصيل.",
            data=order_data,
            status=201,
        )
    except Exception as e:
        return api_response(success=False, message="حدث خطأ أثناء تسجيل الطلب", errors=[str(e)], status=400)


@router.get("/{slug}", response={200: ApiResponseSchema[GameDetailSchema], 404: ApiResponseSchema[None]})
def get_game_detail(request, slug: str):
    """
    Product details page with multi-photo gallery.
    """
    try:
        game = Game.objects.prefetch_related("images").get(slug=slug, is_active=True)
        data = serialize_game(game, request, include_gallery=True)
        return api_response(success=True, message="تم جلب تفاصيل اللعبة بنجاح", data=data, status=200)
    except Game.DoesNotExist:
        return api_response(success=False, message="اللعبة غير موجودة", errors=["اللعبة غير موجودة"], status=404)


# ---------------- Admin Operations ----------------

@router.post("/", auth=AdminAuth(), response={201: ApiResponseSchema[GameCardSchema], 400: ApiResponseSchema[None]})
def create_game(
    request,
    title: str = Form(...),
    price: float = Form(...),
    description: str = Form(...),
    tags: Optional[str] = Form(""),
    thumbnail: UploadedFile = File(...),
):
    """Admin: Add a new educational game to the store."""
    try:
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
            tags=tags or "",
            thumbnail=thumbnail,
            is_active=True,
        )
        return api_response(
            success=True,
            message="تمت إضافة اللعبة بنجاح",
            data=serialize_game(game, request),
            status=201,
        )
    except Exception as e:
        return api_response(success=False, message="فشل إضافة اللعبة", errors=[str(e)], status=400)


@router.delete("/{game_id}", auth=AdminAuth(), response={200: ApiResponseSchema[None], 404: ApiResponseSchema[None]})
def delete_game(request, game_id: int):
    """Admin: Delete an educational game."""
    try:
        game = Game.objects.get(id=game_id)
        game.delete()
        return api_response(success=True, message="تم حذف اللعبة بنجاح", status=200)
    except Game.DoesNotExist:
        return api_response(success=False, message="اللعبة غير موجودة", errors=["اللعبة غير موجودة"], status=404)


@router.get("/admin/orders", auth=AdminAuth(), response=ApiResponseSchema[List[GameOrderSchema]])
def list_cod_orders(request, status: Optional[str] = None):
    """Admin: List COD store orders with optional status filtering."""
    orders = GameOrder.objects.select_related("game").all().order_by("-created_at")
    if status and status in GameOrder.OrderStatus.values:
        orders = orders.filter(status=status)

    items = [serialize_game_order(o) for o in orders]
    return api_response(success=True, message="تم جلب الطلبات بنجاح", data=items, status=200)


@router.post("/admin/orders/{order_id}/status", auth=AdminAuth(), response={200: ApiResponseSchema[None], 400: ApiResponseSchema[None], 404: ApiResponseSchema[None]})
def update_order_status(request, order_id: int, data: UpdateOrderStatusSchema):
    """Admin: Update the status of a COD game order."""
    if data.status not in GameOrder.OrderStatus.values:
        return api_response(success=False, message="حالة الطلب غير صالحة", errors=["حالة الطلب غير صالحة"], status=400)

    try:
        order = GameOrder.objects.get(id=order_id)
        order.status = data.status
        order.save()
        return api_response(success=True, message="تم تحديث حالة الطلب بنجاح", status=200)
    except GameOrder.DoesNotExist:
        return api_response(success=False, message="الطلب غير موجود", errors=["الطلب غير موجود"], status=404)
