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

    if not history:
        history.append({
            "title": user_msg[:40],
            "messages": []
        })

    # nếu là Chat mới và chưa có tin nhắn
    if (
        history[-1]["title"] == "Chat mới"
        and len(history[-1]["messages"]) == 0
    ):
        history[-1]["title"] = user_msg[:40]

    history[-1]["messages"].append({
        "user": user_msg,
        "bot": bot_reply
    })

    with open(CHAT_HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(
            history,
            f,
            ensure_ascii=False,
            indent=2
        )


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

    points = []

    for r in rows:
        points.append({
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

    return JsonResponse(points, safe=False)
def get_report_data(request):

    from_date = request.GET.get("from_date")
    to_date = request.GET.get("to_date")
    river = request.GET.get("river")
    level = request.GET.get("level")

    conn = psycopg2.connect(
        dbname="webgis_nuoc",
        user="postgres",
        password="123456",
        host="localhost",
        port="5432"
    )

    cur = conn.cursor()

    query = """
        SELECT
            segment_name,
            ph,
            do_val,
            bod5,
            cod,
            nh4,
            coliform,
            polluted_count,
            report_date
        FROM warnings
        WHERE 1=1
    """

    params = []

    if from_date:
        query += " AND report_date >= %s"
        params.append(from_date + " 00:00:00")

    if to_date:
        query += " AND report_date <= %s"
        params.append(to_date + " 23:59:59")

    if river:
        query += " AND segment_name = %s"
        params.append(river)

    if level == "normal":
        query += " AND polluted_count = 0"

    elif level == "medium":
        query += " AND polluted_count BETWEEN 1 AND 3"

    elif level == "high":
        query += " AND polluted_count = 4"

    elif level == "veryhigh":
        query += " AND polluted_count >= 5"

    query += """
    ORDER BY report_date DESC
    LIMIT 1300
    """

    cur.execute(query, params)

    rows = cur.fetchall()

    total = len(rows)

    polluted = len([
        r for r in rows
        if r[7] > 0
    ])

    normal = len([
        r for r in rows
        if r[7] == 0
    ])

    high_warning = len([
        r for r in rows
        if r[7] == 4
    ])

    very_high_warning = len([
        r for r in rows
        if r[7] >= 5
    ])

    data = []

    for r in rows:

        data.append({
            "segment": r[0],
            "ph": float(r[1]),
            "do": float(r[2]),
            "bod5": float(r[3]),
            "cod": float(r[4]),
            "nh4": float(r[5]),
            "coliform": float(r[6]),
            "polluted_count": int(r[7]),
            "report_date": str(r[8])
        })

    cur.close()
    conn.close()

    return JsonResponse({
        "total": total,
        "polluted": polluted,
        "normal": normal,
        "high_warning": high_warning,
        "very_high_warning": very_high_warning,
        "rate": round(
            polluted * 100 / total, 2
        ) if total else 0,
        "rows": data[:1300]
    })

def get_rivers(request):

    conn = psycopg2.connect(
        dbname="webgis_nuoc",
        user="postgres",
        password="123456",
        host="localhost",
        port="5432"
    )

    cur = conn.cursor()

    cur.execute("""
        SELECT DISTINCT segment_name
        FROM warnings
        ORDER BY segment_name
    """)

    rivers = [r[0] for r in cur.fetchall()]

    cur.close()
    conn.close()

    return JsonResponse(rivers, safe=False)

def get_latest_reports(request):

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
            id,
            segment_name,
            report_date,
            polluted_count
        FROM warnings
        ORDER BY report_date DESC
        LIMIT 100
    """)

    rows = cur.fetchall()

    data = []

    for r in rows:
        data.append({
            "id": r[0],
            "segment_name": r[1],
            "report_date": str(r[2]),
            "polluted_count": r[3]
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

def login_view(request):
    return render(request, "login.html")

def register_view(request):
    return render(request, "register.html")

def report_view(request):
    return render(request, "report.html")

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

            # DO cao nhất
            if "do cao nhất" in message:
                point = max(data, key=lambda x: x.get("do", 0))
                last_point = point
                return reply_and_save(
                    f"Điểm {point['ma_diem']} có DO cao nhất: {point['do']}"
                )

            # COD thấp nhất
            if "cod thấp nhất" in message:
                point = min(data, key=lambda x: x.get("cod", 999))
                last_point = point
                return reply_and_save(
                    f"Điểm {point['ma_diem']} có COD thấp nhất: {point['cod']}"
                )

            # BOD5 thấp nhất
            if "bod5 thấp nhất" in message:
                point = min(data, key=lambda x: x.get("bod5", 999))
                last_point = point
                return reply_and_save(
                    f"Điểm {point['ma_diem']} có BOD5 thấp nhất: {point['bod5']}"
                )

            # NH4 thấp nhất
            if "nh4 thấp nhất" in message:
                point = min(data, key=lambda x: x.get("nh4", 999))
                last_point = point
                return reply_and_save(
                    f"Điểm {point['ma_diem']} có NH4 thấp nhất: {point['nh4']}"
                )

            # Coliform cao nhất
            if "coliform cao nhất" in message:
                point = max(data, key=lambda x: x.get("coliform", 0))
                last_point = point
                return reply_and_save(
                    f"Điểm {point['ma_diem']} có Coliform cao nhất: {point['coliform']}"
                )

            # Coliform thấp nhất
            if "coliform thấp nhất" in message:
                point = min(data, key=lambda x: x.get("coliform", 999999))
                last_point = point
                return reply_and_save(
                    f"Điểm {point['ma_diem']} có Coliform thấp nhất: {point['coliform']}"
                )
            
            # Trung bình pH
            if "ph trung bình" in message:
                avg = sum(x["ph"] for x in data) / len(data)
                return reply_and_save(
                    f"pH trung bình là {avg:.2f}"
                )

            # Trung bình DO
            if "do trung bình" in message:
                avg = sum(x["do"] for x in data) / len(data)
                return reply_and_save(
                    f"DO trung bình là {avg:.2f}"
                )

            # Trung bình COD
            if "cod trung bình" in message:
                avg = sum(x["cod"] for x in data) / len(data)
                return reply_and_save(
                    f"COD trung bình là {avg:.2f}"
                )

            # Trung bình BOD5
            if "bod5 trung bình" in message:
                avg = sum(x["bod5"] for x in data) / len(data)
                return reply_and_save(
                    f"BOD5 trung bình là {avg:.2f}"
                )

            # Trung bình NH4
            if "nh4 trung bình" in message:
                avg = sum(x["nh4"] for x in data) / len(data)
                return reply_and_save(
                    f"NH4 trung bình là {avg:.2f}"
                )

            # DO dưới chuẩn
            if "do dưới chuẩn" in message:
                count = len([
                    x for x in data
                    if x["do"] < 4
                ])

                return reply_and_save(
                    f"Có {count} điểm DO dưới chuẩn."
                )

            # COD vượt chuẩn
            if "cod vượt chuẩn" in message:
                count = len([
                    x for x in data
                    if x["cod"] > 30
                ])

                return reply_and_save(
                    f"Có {count} điểm COD vượt chuẩn."
                )

            # BOD5 vượt chuẩn
            if "bod5 vượt chuẩn" in message:
                count = len([
                    x for x in data
                    if x["bod5"] > 12
                ])

                return reply_and_save(
                    f"Có {count} điểm BOD5 vượt chuẩn."
                )

            # NH4 vượt chuẩn
            if "nh4 vượt chuẩn" in message:
                count = len([
                    x for x in data
                    if x["nh4"] > 0.5
                ])

                return reply_and_save(
                    f"Có {count} điểm NH4 vượt chuẩn."
                )

            if "top 5 cod" in message:

                top = sorted(
                    data,
                    key=lambda x: x["cod"],
                    reverse=True
                )[:5]

                result = "Top 5 COD cao nhất:\n"

                for p in top:
                    result += (
                        f"{p['ma_diem']} : "
                        f"{p['cod']}\n"
                    )

                return reply_and_save(result)
            
            if "nước có tốt không" in message:

                bad = len([
                    x for x in data
                    if x["cod"] > 30
                    or x["bod5"] > 12
                    or x["nh4"] > 0.5
                ])

                if bad > len(data)/2:
                    return reply_and_save(
                        "Chất lượng nước đang ở mức kém."
                    )

                return reply_and_save(
                    "Chất lượng nước đang ở mức tương đối tốt."
                )

            if "thông tin điểm" in message:

                parts = message.split()

                ma = parts[-1].upper()

                for p in data:

                    if p["ma_diem"] == ma:

                        last_point = p

                        return reply_and_save(
                            f"""
                            Điểm {ma}

                            pH: {p['ph']}
                            DO: {p['do']}
                            BOD5: {p['bod5']}
                            COD: {p['cod']}
                            NH4: {p['nh4']}
                            Coliform: {p['coliform']}
                            """
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

                    map_link = f"/map/?point={last_point['ma_diem']}" 

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