"""
BGS Infra — Flask Backend
Railway deployment | Python 3.11+
"""

import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from supabase import create_client, Client
from dotenv import load_dotenv
import resend
from datetime import datetime

load_dotenv()

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# ── Supabase ──────────────────────────────────────────────
SUPABASE_URL: str = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY: str = os.environ.get("SUPABASE_KEY", "")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ── Resend ────────────────────────────────────────────────
resend.api_key = os.environ.get("RESEND_API_KEY", "")
NOTIFY_EMAIL   = os.environ.get("NOTIFY_EMAIL", "")      # uncle's email


# ════════════════════════════════════════════════════════════
#  CONTACT FORM
# ════════════════════════════════════════════════════════════
@app.route("/api/contact", methods=["POST"])
def contact():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data"}), 400

    name    = data.get("name",    "").strip()
    phone   = data.get("phone",   "").strip()
    email   = data.get("email",   "").strip()
    service = data.get("service", "").strip()
    message = data.get("message", "").strip()

    if not name or not phone:
        return jsonify({"error": "Name and phone are required"}), 422

    # Save to Supabase
    try:
        supabase.table("enquiries").insert({
            "name":       name,
            "phone":      phone,
            "email":      email,
            "service":    service,
            "message":    message,
            "status":     "new",
            "created_at": datetime.utcnow().isoformat(),
        }).execute()
    except Exception as e:
        print(f"Supabase error: {e}")
        return jsonify({"error": "Database error"}), 500

    # Send email alert to uncle
    if NOTIFY_EMAIL and resend.api_key:
        try:
            resend.Emails.send({
                "from":    "BGS Infra Enquiry <noreply@bgsinfra.in>",
                "to":      [NOTIFY_EMAIL],
                "subject": f"New Enquiry from {name} — BGS Infra",
                "html":    f"""
                <h2 style="color:#3B2A1A;">New Website Enquiry</h2>
                <table style="border-collapse:collapse;width:100%;font-family:sans-serif;">
                  <tr><td style="padding:10px;background:#F5EDD8;font-weight:bold;width:140px;">Name</td>
                      <td style="padding:10px;border:1px solid #ddd;">{name}</td></tr>
                  <tr><td style="padding:10px;background:#F5EDD8;font-weight:bold;">Phone</td>
                      <td style="padding:10px;border:1px solid #ddd;">{phone}</td></tr>
                  <tr><td style="padding:10px;background:#F5EDD8;font-weight:bold;">Email</td>
                      <td style="padding:10px;border:1px solid #ddd;">{email or '—'}</td></tr>
                  <tr><td style="padding:10px;background:#F5EDD8;font-weight:bold;">Service</td>
                      <td style="padding:10px;border:1px solid #ddd;">{service or '—'}</td></tr>
                  <tr><td style="padding:10px;background:#F5EDD8;font-weight:bold;">Message</td>
                      <td style="padding:10px;border:1px solid #ddd;">{message or '—'}</td></tr>
                </table>
                <p style="margin-top:16px;color:#666;font-size:13px;">
                  Login to admin panel to update status: 
                  <a href="https://YOUR-SITE.vercel.app/admin/index.html">Admin Panel</a>
                </p>
                """,
            })
        except Exception as e:
            print(f"Email error: {e}")   # Don't fail the request if email fails

    return jsonify({"success": True, "message": "Enquiry received"}), 201


# ════════════════════════════════════════════════════════════
#  PROJECTS (public — fetches from Supabase)
# ════════════════════════════════════════════════════════════
@app.route("/api/projects", methods=["GET"])
def get_projects():
    service_type = request.args.get("type")
    try:
        query = supabase.table("projects").select("*").order("year", desc=True)
        if service_type:
            query = query.eq("service_type", service_type)
        result = query.execute()
        return jsonify(result.data), 200
    except Exception as e:
        print(f"Projects error: {e}")
        return jsonify([]), 200


# ════════════════════════════════════════════════════════════
#  ADMIN — Enquiries
# ════════════════════════════════════════════════════════════
@app.route("/api/admin/enquiries", methods=["GET"])
def admin_enquiries():
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if not verify_token(token):
        return jsonify({"error": "Unauthorized"}), 401
    try:
        result = supabase.table("enquiries").select("*")\
                   .order("created_at", desc=True).execute()
        return jsonify(result.data), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/admin/enquiries/<int:enquiry_id>", methods=["PATCH"])
def update_enquiry(enquiry_id):
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if not verify_token(token):
        return jsonify({"error": "Unauthorized"}), 401
    data = request.get_json()
    status = data.get("status")
    if status not in ("new", "contacted", "closed"):
        return jsonify({"error": "Invalid status"}), 422
    try:
        supabase.table("enquiries").update({"status": status})\
          .eq("id", enquiry_id).execute()
        return jsonify({"success": True}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ════════════════════════════════════════════════════════════
#  ADMIN — Projects CRUD
# ════════════════════════════════════════════════════════════
@app.route("/api/admin/projects", methods=["POST"])
def add_project():
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if not verify_token(token):
        return jsonify({"error": "Unauthorized"}), 401
    data = request.get_json()
    try:
        result = supabase.table("projects").insert({
            "title":        data.get("title", ""),
            "service_type": data.get("service_type", ""),
            "location":     data.get("location", ""),
            "description":  data.get("description", ""),
            "image_url":    data.get("image_url", ""),
            "year":         data.get("year", datetime.utcnow().year),
            "is_featured":  data.get("is_featured", False),
        }).execute()
        return jsonify(result.data[0]), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/admin/projects/<int:project_id>", methods=["DELETE"])
def delete_project(project_id):
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if not verify_token(token):
        return jsonify({"error": "Unauthorized"}), 401
    try:
        supabase.table("projects").delete().eq("id", project_id).execute()
        return jsonify({"success": True}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ════════════════════════════════════════════════════════════
#  ADMIN — Login (simple token)
# ════════════════════════════════════════════════════════════
@app.route("/api/admin/login", methods=["POST"])
def admin_login():
    data     = request.get_json()
    password = data.get("password", "")
    # Compare against env var — never hardcode passwords
    if password == os.environ.get("ADMIN_PASSWORD", ""):
        import secrets, hashlib, time
        token = hashlib.sha256(
            f"{password}{time.time()}{secrets.token_hex(16)}".encode()
        ).hexdigest()
        # Store token in Supabase for validation
        supabase.table("admin_tokens").upsert({
            "token":      token,
            "created_at": datetime.utcnow().isoformat()
        }).execute()
        return jsonify({"token": token}), 200
    return jsonify({"error": "Invalid password"}), 401


def verify_token(token: str) -> bool:
    if not token:
        return False
    try:
        result = supabase.table("admin_tokens").select("token")\
                   .eq("token", token).execute()
        return len(result.data) > 0
    except:
        return False


# ════════════════════════════════════════════════════════════
#  HEALTH CHECK
# ════════════════════════════════════════════════════════════
@app.route("/", methods=["GET"])
def health():
    return jsonify({"status": "BGS Infra API running ✓"}), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
