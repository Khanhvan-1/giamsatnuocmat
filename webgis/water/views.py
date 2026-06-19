from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
import psycopg2
import json
import os
import requests
from django.views.decorators.http import require_http_methods

# =========================
# BIẾN TOÀN CỤC
# =========================
last_point = None
CHAT_HISTORY_FILE = "chat_history.json"


# =========================
# HÀM LỊCH SỬ CHAT
# =========================
def load_chat_history():
    if os.path.exists(CHAT_HISTORY_FILE):
        with open(CHAT_HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_chat(user_msg, bot_reply):
    history = load_chat_history()

    # nếu chưa có session nào → tạo mới
    if not history:
        history.append({
            "title": user_msg,
            "messages": []
        })

    # thêm vào session cuối cùng
    history[-1]["messages"].append({
        "user": user_msg,
        "bot": bot_reply
    })

    with open(CHAT_HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


def get_chat_history(request):
    return JsonResponse(load_chat_history(), safe=False)


@csrf_exempt
def clear_chat_history(request):
    if request.method == "POST":
        with open(CHAT_HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump([], f)

        return JsonResponse({
            "message": "Đã xoá lịch sử chat."
        })

    return JsonResponse({
        "message": "Dùng POST để xoá."
    })

@csrf_exempt
def new_chat(request):
    if request.method == "POST":
        history = load_chat_history()

        history.append({
            "title": "Chat mới",
            "messages": []
        })

        with open(CHAT_HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)

        return JsonResponse({"ok": True})

    return JsonResponse({"ok": False})

# =========================
# LẤY DỮ LIỆU ĐIỂM QUAN TRẮC
# =========================
def get_points(request):

    conn = psycopg2.connect(
        dbname="webgis_nuoc",
        user="postgres",
        password="123456",
        host="localhost",
        port="5432"
    )

    cur = conn.cursor()

    cur.execute("""
        SELECT
            ma_diem,
            ph,
            "do",
            bod5,
            cod,
            nh4,
            caliform,
            ST_AsGeoJSON(geom)
        FROM diem_quan_trac_clean
    """)

    rows = cur.fetchall()
    data = []

    for r in rows:
        data.append({
            "ma_diem": r[0],
            "ph": r[1],
            "do": r[2],
            "bod5": r[3],
            "cod": r[4],
            "nh4": r[5],
            "caliform": r[6],
            "geometry": json.loads(r[7])
        })

    cur.close()
    conn.close()

    return JsonResponse(data, safe=False)


# =========================
# MAP
# =========================
def map_view(request):
    return render(request, "map.html")


# =========================
# DASHBOARD
# =========================
def dashboard(request):
    return render(request, "dashboard.html")


# =========================
# CHATBOT
# =========================
@csrf_exempt
def chatbot(request):
    global last_point

    if request.method == "POST":
        try:
            body = json.loads(request.body)

            message = body.get("message", "").lower()
            data = body.get("data", [])

            # helper lưu chat
            def reply_and_save(text):
                save_chat(message, text)
                return JsonResponse({
                    "reply": text
                })

            # =====================
            # 1. số lượng điểm
            # =====================
            if any(x in message for x in [
                "bao nhiêu điểm",
                "mấy điểm",
                "số điểm",
                "bao nhiêu điểm quan trắc"
            ]):
                return reply_and_save(
                    f"Hiện có {len(data)} điểm quan trắc."
                )

            # =====================
            # 2. COD cao nhất
            # =====================
            if "cod cao nhất" in message:
                point = max(data, key=lambda x: x.get("cod", 0))
                last_point = point
                return reply_and_save(
                    f"Điểm {point['ma_diem']} có COD cao nhất: {point['cod']}"
                )

            # =====================
            # 3. BOD5 cao nhất
            # =====================
            if "bod5 cao nhất" in message or "bod cao nhất" in message:
                point = max(data, key=lambda x: x.get("bod5", 0))
                last_point = point
                return reply_and_save(
                    f"Điểm {point['ma_diem']} có BOD5 cao nhất: {point['bod5']}"
                )

            # =====================
            # 4. NH4 cao nhất
            # =====================
            if "nh4 cao nhất" in message:
                point = max(data, key=lambda x: x.get("nh4", 0))
                last_point = point
                return reply_and_save(
                    f"Điểm {point['ma_diem']} có NH4 cao nhất: {point['nh4']}"
                )

            # =====================
            # 5. Caliform cao nhất
            # =====================
            if "caliform cao nhất" in message:
                point = max(data, key=lambda x: x.get("caliform", 0))
                last_point = point
                return reply_and_save(
                    f"Điểm {point['ma_diem']} có Caliform cao nhất: {point['caliform']}"
                )

            # =====================
            # 6. DO thấp nhất
            # =====================
            if "do thấp nhất" in message:
                point = min(data, key=lambda x: x.get("do", 999))
                last_point = point
                return reply_and_save(
                    f"Điểm {point['ma_diem']} có DO thấp nhất: {point['do']}"
                )

            # =====================
            # 7. pH cao nhất
            # =====================
            if "ph cao nhất" in message:
                point = max(data, key=lambda x: x.get("ph", 0))
                last_point = point
                return reply_and_save(
                    f"Điểm {point['ma_diem']} có pH cao nhất: {point['ph']}"
                )

            # =====================
            # 8. pH thấp nhất
            # =====================
            if "ph thấp nhất" in message:
                point = min(data, key=lambda x: x.get("ph", 999))
                last_point = point
                return reply_and_save(
                    f"Điểm {point['ma_diem']} có pH thấp nhất: {point['ph']}"
                )

            # =====================
            # 9. điểm ô nhiễm nhất
            # =====================
            if "ô nhiễm nhất" in message:
                point = max(
                    data,
                    key=lambda x:
                        x.get("cod", 0)
                        + x.get("bod5", 0)
                        + x.get("nh4", 0)
                )
                last_point = point
                return reply_and_save(
                    f"Điểm ô nhiễm nhất là {point['ma_diem']}."
                )

            # =====================
            # 10. điểm sạch nhất
            # =====================
            if "sạch nhất" in message:
                point = min(
                    data,
                    key=lambda x:
                        x.get("cod", 0)
                        + x.get("bod5", 0)
                        + x.get("nh4", 0)
                )
                last_point = point
                return reply_and_save(
                    f"Điểm sạch nhất là {point['ma_diem']}."
                )

            # =====================
            # 11. hỏi tọa độ
            # =====================
            if "tọa độ" in message or "vị trí" in message or "ở đâu" in message:
                if last_point:
                    lng = last_point["geometry"]["coordinates"][0]
                    lat = last_point["geometry"]["coordinates"][1]

                    return reply_and_save(
                        f"""Điểm {last_point['ma_diem']} có tọa độ:

Lat: {lat}
Lng: {lng}
"""
                    )
                else:
                    return reply_and_save(
                        "Bạn chưa hỏi điểm nào trước đó."
                    )

            # =====================
            # 12. gửi link xem map
            # =====================
            if (
                "gửi link" in message
                or "xem trên bản đồ" in message
                or "mở bản đồ" in message
                or "cho tôi xem map" in message
                or "cho tôi coi" in message
            ):
                if last_point:
                    lng = last_point["geometry"]["coordinates"][0]
                    lat = last_point["geometry"]["coordinates"][1]

                    map_link = f"http://127.0.0.1:8000/?center={lat},{lng}"

                    return reply_and_save(
                        f'<a href="{map_link}" target="_blank">📍 Xem trên bản đồ</a>'
                    )
                else:
                    return reply_and_save(
                        "Bạn chưa hỏi điểm nào trước đó."
                    )

            # =====================
            # 13. hỏi từng điểm
            # =====================
            for point in data:
                ma = point["ma_diem"].lower()

                if ma in message:
                    last_point = point

                    return reply_and_save(
                        f"""Điểm {point['ma_diem']}:

pH: {point['ph']}
DO: {point['do']}
BOD5: {point['bod5']}
COD: {point['cod']}
NH4: {point['nh4']}
Caliform: {point['caliform']}
"""
                    )

            return reply_and_save(
                "Tôi chưa hiểu câu hỏi này."
            )

        except Exception as e:
            return JsonResponse({
                "reply": f"Lỗi: {str(e)}"
            })

    return JsonResponse({
        "reply": "Chatbot API đang hoạt động."
    })

@require_http_methods(["GET"])
@csrf_exempt
def proxy_nominatim_search(request):
    q = request.GET.get('q', '')
    limit = request.GET.get('limit', 8)
    countrycodes = request.GET.get('countrycodes', 'vn')
    viewbox = request.GET.get('viewbox', '')
    lat = request.GET.get('lat', '')
    lon = request.GET.get('lon', '')
    radius = request.GET.get('radius', '')
    
    url = 'https://nominatim.openstreetmap.org/search'
    params = {
        'format': 'json',
        'q': q,
        'limit': limit,
        'countrycodes': countrycodes,
        'addressdetails': 1,
    }
    if viewbox:
        params['viewbox'] = viewbox
        params['bounded'] = 1
    if lat and lon:
        params['lat'] = lat
        params['lon'] = lon
        params['radius'] = radius if radius else 5000
    
    headers = {'User-Agent': 'WaterQualityGIS/1.0 (nguyenhungvankhanh09012004@gmail.com)'}
    try:
        print(f"🔍 Gọi search: {url} với params {params}")
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        resp.raise_for_status()
        return JsonResponse(resp.json(), safe=False)
    except Exception as e:
        print(f"❌ Lỗi proxy search: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)

@require_http_methods(["GET"])
@csrf_exempt
def proxy_nominatim_reverse(request):
    lat = request.GET.get('lat')
    lon = request.GET.get('lon')
    if not lat or not lon:
        return JsonResponse({'error': 'Missing lat/lon'}, status=400)
    
    url = 'https://nominatim.openstreetmap.org/reverse'
    params = {
        'format': 'json',
        'lat': lat,
        'lon': lon,
        'zoom': 18,
        'addressdetails': 1,
    }
    headers = {'User-Agent': 'WaterQualityGIS/1.0 (nguyenhungvankhanh09012004@gmail.com)'}
    try:
        print(f"🔍 Gọi reverse: lat={lat}, lon={lon}")
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        resp.raise_for_status()
        return JsonResponse(resp.json())
    except Exception as e:
        print(f"❌ Lỗi proxy reverse: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)