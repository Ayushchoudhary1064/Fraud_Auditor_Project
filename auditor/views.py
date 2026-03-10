from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse
import os
import pandas as pd
import networkx as nx
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from .models import Claim, CustomUser 

# Get the active user model
User = get_user_model()

# --- SMART PATH LOGIC ---
# Local Windows path for your desktop
LOCAL_PATH = r"C:\Users\welcome\OneDrive\Desktop\data\cleaned_claims_dataset.csv"
# Replit/Server path (Project Root)
SERVER_PATH = os.path.join(settings.BASE_DIR, 'cleaned_claims_dataset.csv')

# Automatically select the path that exists
if os.path.exists(LOCAL_PATH):
    DATA_PATH = LOCAL_PATH
else:
    DATA_PATH = SERVER_PATH

# --- Helper Function for Network-Based Fraud Assessment ---
def calculate_fraud_score_and_notes(claim):
    score = 0
    notes = []
    df = None

    try:
        if not os.path.exists(DATA_PATH):
            raise FileNotFoundError("Data file not found. Network checks skipped.")

        df = pd.read_csv(DATA_PATH)
        df.columns = df.columns.str.strip().str.lower()
    except Exception as e:
        notes.append(f"Data error: {str(e)}.")
        df = None 

    if df is not None:
        try:
            G = nx.Graph()
            for provider_id, group in df.groupby('provider_id'):
                patients = group['patient_id'].unique()
                for i, p1 in enumerate(patients):
                    for p2 in patients[i + 1:]:
                        if G.has_edge(p1, p2):
                            G[p1][p2]['weight'] += 1
                        else:
                            G.add_edge(p1, p2, weight=1)

            from networkx.algorithms.community import greedy_modularity_communities
            communities = list(greedy_modularity_communities(G))

            target_id = claim.patient_id
            for community in communities:
                if target_id in community:
                    size = len(community)
                    if size > settings.FRAUD_COMMUNITY_SIZE_THRESHOLD:
                        score += 1
                        notes.append(f"Suspicious network: Large community ({size}).")
                    break 
        except Exception as e:
            notes.append(f"Network error: {str(e)}.")

    if df is not None and 'provider_id' in df.columns:
        p_count = len(df[df['provider_id'] == claim.provider_id])
        if p_count > settings.FRAUD_PROVIDER_CLAIM_COUNT_THRESHOLD:
            score += 1
            notes.append(f"High Provider volume: {p_count} claims.")

    if hasattr(settings, 'FRAUD_PROCEDURE_CODE_PREFIXES'):
        for prefix in settings.FRAUD_PROCEDURE_CODE_PREFIXES:
            if claim.procedure_code and claim.procedure_code.startswith(prefix):
                score += 1
                notes.append(f"Flagged Proc Code: {claim.procedure_code}.")
                break

    return score, notes

# --- Authentication Views ---

def index(request):
    return render(request, 'index.html')

def login_view(request):
    if request.method == "POST":
        u, p = request.POST.get("username"), request.POST.get("password")
        user = authenticate(request, username=u, password=p)
        if user:
            auth_login(request, user)
            return redirect('home')
        messages.error(request, "Invalid credentials")
    return render(request, "login.html")

def register_view(request):
    if request.method == "POST":
        d = request.POST
        if d.get("password") != d.get("confirm_password"):
            messages.error(request, "Passwords do not match")
            return render(request, "signup.html")
        try:
            User.objects.create_user(
                username=d.get("username"), email=d.get("email"), password=d.get("password"),
                first_name=d.get("first_name"), last_name=d.get("last_name"), gender=d.get("gender")
            )
            messages.success(request, "Success! Please login.")
            return redirect('login')
        except Exception as e:
            messages.error(request, str(e))
    return render(request, 'signup.html')

@login_required
def home(request):
    return render(request, 'home.html')

@login_required
def logout_view(request):
    auth_logout(request)
    return redirect('login')

# --- User Claim Views ---

@login_required
def submit_claim(request):
    if request.method == "POST":
        fields = ['claim_id', 'patient_id', 'provider_id', 'claim_amount', 'num_visits', 
                  'hospitalized', 'days_admitted', 'age', 'gender', 'procedure_code', 'diagnosis_code']
        data = {f: request.POST.get(f) for f in fields}
        try:
            data['claim_amount'] = float(data['claim_amount'])
            data['hospitalized'] = data.get('hospitalized') == 'on'
            Claim.objects.create(user=request.user, **data)
            messages.success(request, "Claim submitted!")
            return redirect('view_status')
        except Exception as e:
            messages.error(request, f"Error: {str(e)}")
    return render(request, 'submit.html')

@login_required
def view_status(request):
    claims = Claim.objects.filter(user=request.user).order_by('-submitted_at')
    return render(request, 'viewstatus.html', {'claims': claims, 'latest_claim': claims.first()})

@login_required
def view_user_profile(request):
    return render(request, 'viewuserprofile.html', {'user': request.user})

# --- Admin Views ---

def admin_login_view(request):
    if request.method == "POST":
        if request.POST.get("username") == "admin" and request.POST.get("password") == "root":
            request.session['is_admin'] = True
            return redirect('admin_home')
        messages.error(request, "Invalid admin credentials.")
    return render(request, "admin_login.html")

def admin_home(request):
    if not request.session.get('is_admin'): return redirect('admin_login')
    return render(request, 'admin.html')

def admin_manage_users(request):
    if not request.session.get('is_admin'): return redirect('admin_login')
    users = User.objects.all().order_by('username')
    return render(request, 'admin_manage_users.html', {'users': users})

def admin_delete_user(request, user_id):
    if not request.session.get('is_admin'): return redirect('admin_login')
    try:
        user = User.objects.get(id=user_id)
        if user.username != "admin":
            user.delete()
            messages.success(request, "User deleted.")
    except: pass
    return redirect('admin_manage_users')

def admin_claim_list(request):
    if not request.session.get('is_admin'): return redirect('admin_login')
    claims = Claim.objects.select_related('user').all().order_by('-submitted_at')
    return render(request, 'admin_claim_list.html', {'claims': claims})

@never_cache
def admin_model_execution(request):
    if not request.session.get('is_admin'): return redirect('admin_login')
    ctx = {}
    try:
        df = pd.read_csv(DATA_PATH)
        G = nx.Graph()
        for _, g in df.groupby('provider_id'):
            p = g['patient_id'].unique()
            for i, p1 in enumerate(p):
                for p2 in p[i+1:]: G.add_edge(p1, p2)
        from networkx.algorithms.community import greedy_modularity_communities
        suspicious = [list(c) for c in greedy_modularity_communities(G) if len(c) > settings.FRAUD_COMMUNITY_SIZE_THRESHOLD]
        ctx.update({'total_nodes': G.number_of_nodes(), 'num_suspicious': len(suspicious), 'suspicious_communities': suspicious})
    except Exception as e: ctx['error'] = str(e)
    return render(request, 'admin_model_execution.html', ctx)

@never_cache
def admin_covisit_network(request):
    if not request.session.get('is_admin'): return redirect('admin_login')
    ctx = {}
    try:
        df = pd.read_csv(DATA_PATH)
        G = nx.Graph()
        for _, g in df.groupby('provider_id'):
            p = g['patient_id'].unique()
            for i, p1 in enumerate(p):
                for p2 in p[i+1:]: G.add_edge(p1, p2)

        plt.figure(figsize=(8, 8))
        nx.draw(G, node_size=20, edge_color='silver')
        
        # Save to static
        path = os.path.join(settings.BASE_DIR, 'static', 'network.png')
        os.makedirs(os.path.dirname(path), exist_ok=True)
        plt.savefig(path)
        plt.close()

        ctx['network_image'] = 'network.png'
        ctx['network_info'] = {'total_nodes': G.number_of_nodes(), 'total_edges': G.number_of_edges()}
    except Exception as e: messages.error(request, str(e))
    return render(request, 'admin_covisit_network.html', ctx)

@never_cache
def admin_fraud_report(request):
    if not request.session.get('is_admin'): return redirect('admin_login')
    return render(request, 'admin_fraud_report.html')

@never_cache
def assess_claim_status(request, claim_id):
    if not request.session.get('is_admin'): return redirect('admin_login')
    claim = get_object_or_404(Claim, id=claim_id)
    score, notes = calculate_fraud_score_and_notes(claim)
    claim.status = "Rejected" if score >= settings.FRAUD_TOTAL_SCORE_THRESHOLD else "Accepted"
    claim.notes = f"Score: {score}. " + "; ".join(notes)
    claim.save()
    return redirect('admin_claim_list')

def admin_logout(request):
    request.session.flush()
    return redirect('admin_login')