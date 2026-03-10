# auditor/views.py
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.conf import settings # IMPORT THIS LINE TO ACCESS SETTINGS
import os
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
from .models import Claim, CustomUser # Ensure CustomUser and Claim are imported

# Get the active user model
User = get_user_model()

# IMPORTANT: Ensure this path is correct and accessible from where Django runs
# Consider using a more robust path like os.path.join(settings.BASE_DIR, 'data', 'cleaned_claims_dataset.csv')
# for better deployment practices. For now, keeping your original as requested.
DATA_PATH = r"C:\Users\welcome\OneDrive\Desktop\data\cleaned_claims_dataset.csv"

# --- NEW Helper Function for Network-Based Fraud Assessment ---
def calculate_fraud_score_and_notes(claim):
    """
    Calculates a fraud score for a single claim based *only* on network and other
    non-monetary factors.
    Returns the score and a list of notes explaining the contributing factors.
    """
    score = 0
    notes = []

    # --- Load Data for Network/Frequency Checks ---
    df = None
    try:
        if not os.path.exists(DATA_PATH):
            raise FileNotFoundError(f"Data file not found at {DATA_PATH}. Network/Frequency checks skipped.")

        df = pd.read_csv(DATA_PATH)
        df.columns = df.columns.str.strip().str.lower()

        # Only 'patient_id' and 'provider_id' are strictly required for network-based checks
        required_cols_for_network_checks = {'patient_id', 'provider_id'}
        if not required_cols_for_network_checks.issubset(df.columns):
            notes.append(f"Warning: Missing required columns in CSV for network checks: {required_cols_for_network_checks - set(df.columns)}. Network checks skipped.")
            df = None # Invalidate df to skip dependent checks
    except Exception as e:
        notes.append(f"Error loading data for network/frequency analysis: {str(e)}. Some checks skipped.")
        df = None # Invalidate df if there's an error

    # --- 1. Community Size Check (from network analysis) ---
    if df is not None and 'patient_id' in df.columns and 'provider_id' in df.columns:
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

            target_patient_id = claim.patient_id
            patient_community_size = 0

            for community in communities:
                if target_patient_id in community:
                    patient_community_size = len(community)
                    if patient_community_size > settings.FRAUD_COMMUNITY_SIZE_THRESHOLD:
                        score += 1
                        notes.append(f"Suspicious network activity: Patient in large community ({patient_community_size} members, threshold > {settings.FRAUD_COMMUNITY_SIZE_THRESHOLD}).")
                    else:
                        notes.append(f"Clean network activity: Patient in community of size {patient_community_size}.")
                    break # Patient found in a community
            if patient_community_size == 0:
                     notes.append(f"Patient {target_patient_id} not found in any detected community.")

        except Exception as e:
            notes.append(f"Error during community detection for patient {claim.patient_id}: {str(e)}.")
    else:
        notes.append("Community size check skipped due to missing data or columns.")


    # --- 2. Provider Frequency Check (still useful, but less critical than network) ---
    if df is not None and 'provider_id' in df.columns:
        if claim.provider_id:
            provider_claims = df[df['provider_id'] == claim.provider_id]
            if len(provider_claims) > settings.FRAUD_PROVIDER_CLAIM_COUNT_THRESHOLD:
                score += 1
                notes.append(f"Provider '{claim.provider_id}' has high number of claims: {len(provider_claims)} (exceeds threshold {settings.FRAUD_PROVIDER_CLAIM_COUNT_THRESHOLD}).")
            else:
                    notes.append(f"Provider '{claim.provider_id}' has {len(provider_claims)} claims (within threshold).")
        else:
            notes.append("Provider ID not available for frequency check.")
    else:
        notes.append("Provider frequency check skipped due to missing data or columns.")

    # --- 3. Suspicious Procedure Code (from Claim Model) ---
    # Assuming settings.FRAUD_PROCEDURE_CODE_PREFIXES is defined in your settings.py
    if hasattr(settings, 'FRAUD_PROCEDURE_CODE_PREFIXES'):
        found_proc_code_match = False
        for prefix in settings.FRAUD_PROCEDURE_CODE_PREFIXES:
            if claim.procedure_code and claim.procedure_code.startswith(prefix):
                score += 1
                notes.append(f"Suspicious procedure code '{claim.procedure_code}' matches prefix '{prefix}'.")
                found_proc_code_match = True
                break
        if not found_proc_code_match:
            notes.append(f"Procedure code '{claim.procedure_code}' is not flagged as suspicious.")
    else:
        notes.append("FRAUD_PROCEDURE_CODE_PREFIXES not defined in settings.")


    # --- 4. Suspicious Diagnosis Code (from Claim Model) ---
    # Assuming settings.FRAUD_DIAGNOSIS_CODE_PREFIXES is defined in your settings.py
    if hasattr(settings, 'FRAUD_DIAGNOSIS_CODE_PREFIXES'):
        found_diag_code_match = False
        for prefix in settings.FRAUD_DIAGNOSIS_CODE_PREFIXES:
            if claim.diagnosis_code and claim.diagnosis_code.startswith(prefix):
                score += 1
                notes.append(f"Suspicious diagnosis code '{claim.diagnosis_code}' matches prefix '{prefix}'.")
                found_diag_code_match = True
                break
        if not found_diag_code_match:
            notes.append(f"Diagnosis code '{claim.diagnosis_code}' is not flagged as suspicious.")
    else:
        notes.append("FRAUD_DIAGNOSIS_CODE_PREFIXES not defined in settings.")

    # --- Other potential non-amount based checks (examples) ---
    # if claim.hospitalized and claim.days_admitted > settings.FRAUD_LONG_HOSPITAL_STAY_THRESHOLD:
    #     score += 1
    #     notes.append(f"Long hospital stay: {claim.days_admitted} days.")

    # if claim.age < settings.FRAUD_YOUNG_AGE_THRESHOLD or claim.age > settings.FRAUD_OLD_AGE_THRESHOLD:
    #     score += 1
    #     notes.append(f"Unusual age for claim: {claim.age} years.")

    return score, notes

# --- Views ---

# Renamed index_view to index for consistency with urls.py
def index(request):
    return render(request, 'index.html')

def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user:
            auth_login(request, user)
            return redirect('home') # Redirect to the specific 'home' URL
        else:
            messages.error(request, "Invalid credentials") # Use messages for consistency
            return render(request, "login.html", {'error': "Invalid credentials"})
    return render(request, "login.html")

def register_view(request):
    if request.method == "POST":
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        username = request.POST.get("username")
        email = request.POST.get("email")
        gender = request.POST.get("gender") # Correctly retrieved from POST
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password") # Correctly retrieved from POST (HTML name fixed)

        if password != confirm_password:
            messages.error(request, "Passwords do not match") # Use messages
            return render(request, "signup.html", {'error': "Passwords do not match"})

        if User.objects.filter(username=username).exists():
            messages.error(request, f"Username '{username}' already exists") # Use messages
            return render(request, "signup.html", {'error': "Username already exists"})

        try:
            # Pass gender to create_user, which now expects it in CustomUser model
            User.objects.create_user(username=username, email=email, password=password,
                                     first_name=first_name, last_name=last_name, gender=gender)
            messages.success(request, "Registration successful! Please log in.")
            return redirect('login')
        except Exception as e:
            messages.error(request, f"Registration failed: {str(e)}")
            return render(request, "signup.html", {'error': f"Registration failed: {str(e)}"})
    return render(request, 'signup.html')

@login_required
@never_cache
def home(request):
    # This renders home.html after user login
    return render(request, 'home.html')

@login_required
@never_cache
def submit_claim(request):
    if request.method == "POST":
        # Removed 'paid_amount' from the fields list
        fields = ['claim_id', 'patient_id', 'provider_id', 'claim_amount', 'num_visits', 'hospitalized',
                  'days_admitted', 'age', 'gender', 'procedure_code', 'diagnosis_code']
        claim_data = {field: request.POST.get(field) for field in fields}

        # Removed 'paid_amount' from the required_fields_check
        required_fields_check = ['claim_id', 'patient_id', 'provider_id',
                                 'claim_amount', 'procedure_code', 'diagnosis_code']
        if not all(claim_data.get(field) for field in required_fields_check):
            messages.error(request, "All required fields must be filled.")
            return render(request, 'submit.html', {'claim_data': claim_data}) # Pass back data to repopulate form

        # Convert numeric fields to appropriate types, handle potential errors
        try:
            claim_data['claim_amount'] = float(claim_data['claim_amount'])
            # Removed conversion for 'paid_amount'
            # Ensure boolean for hospitalized
            claim_data['hospitalized'] = True if claim_data.get('hospitalized') == 'on' else False
            claim_data['num_visits'] = int(claim_data['num_visits']) if claim_data.get('num_visits') else None
            claim_data['days_admitted'] = int(claim_data['days_admitted']) if claim_data.get('days_admitted') else None
            claim_data['age'] = int(claim_data['age']) if claim_data.get('age') else None

        except ValueError as e:
            messages.error(request, f"Invalid numeric input: {e}. Please check Claim Amount, Num Visits, Days Admitted, Age.")
            return render(request, 'submit.html', {'claim_data': claim_data})

        # Set paid_amount to None or a default if your model requires it but it's not provided by user
        # This assumes your Claim model can handle paid_amount being nullable or having a default.
        claim_data['paid_amount'] = None # Explicitly set to None as it's not coming from the form

        Claim.objects.create(user=request.user, **claim_data)
        messages.success(request, "Claim submitted successfully! Admin will review its status.")
        return redirect('view_status')

    return render(request, 'submit.html')

@login_required
@never_cache
def logout_view(request):
    auth_logout(request)
    messages.success(request, "You have been logged out successfully!")
    return redirect('login')

def admin_login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        if username == "admin" and password == "root": # Hardcoded admin credentials
            request.session['is_admin'] = True
            messages.success(request, "Admin logged in successfully!")
            return redirect('admin_home')
        else:
            messages.error(request, "Invalid admin credentials.") # Use messages
            return render(request, "admin_login.html", {'error': "Invalid admin credentials."})
    return render(request, "admin_login.html")

@never_cache
def admin_home(request):
    if not request.session.get('is_admin'):
        messages.error(request, "Admin login required.")
        return redirect('admin_login')
    return render(request, 'admin.html')

@login_required
@never_cache
def view_status(request):
    # Fetch all claims for the user, ordered by most recent first
    all_claims = Claim.objects.filter(user=request.user).order_by('-submitted_at')

    # Get the single most recent claim if it exists
    latest_claim = all_claims.first()

    return render(request, 'viewstatus.html', {
        'claims': all_claims,
        'latest_claim': latest_claim, # Pass the most recent claim separately
    })

@login_required
@never_cache
def view_user_profile(request):
    return render(request, 'viewuserprofile.html', {'user': request.user})

@never_cache
def admin_manage_users(request):
    if not request.session.get('is_admin'):
        messages.error(request, "Admin login required.")
        return redirect('admin_login')

    users = User.objects.all().order_by('username')

    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        password = request.POST.get("password")

        if not all([username, email, first_name, last_name, password]):
            messages.error(request, "All fields are required to add a user.")
        elif User.objects.filter(username=username).exists():
            messages.error(request, f"Username '{username}' already exists.")
        else:
            try:
                User.objects.create_user(username=username, email=email, password=password,
                                         first_name=first_name, last_name=last_name)
                messages.success(request, f"User '{username}' added successfully.")
            except Exception as e:
                messages.error(request, f"Error adding user: {str(e)}")

        return redirect('admin_manage_users')

    return render(request, 'admin_manage_users.html', {'users': users})

@never_cache
def admin_delete_user(request, user_id):
    if not request.session.get('is_admin'):
        messages.error(request, "Admin login required.")
        return redirect('admin_login')
    try:
        user = User.objects.get(id=user_id)
        if user.username == "admin": # Prevent deleting the default admin user
            messages.error(request, "Cannot delete the default 'admin' user.")
        else:
            user.delete()
            messages.success(request, "User deleted successfully.")
    except User.DoesNotExist:
        messages.error(request, "User not found.")
    return redirect('admin_manage_users')

@never_cache
def admin_claim_list(request):
    if not request.session.get('is_admin'):
        messages.error(request, "Admin login required.")
        return redirect('admin_login')
    claims = Claim.objects.select_related('user').all().order_by('-submitted_at')
    return render(request, 'admin_claim_list.html', {'claims': claims})

@never_cache
def admin_model_execution(request):
    if not request.session.get('is_admin'):
        messages.error(request, "Admin login required.")
        return redirect('admin_login')

    context = {}

    try:
        df = pd.read_csv(DATA_PATH)
        df.columns = df.columns.str.strip().str.lower()

        required_cols = {'provider_id', 'patient_id'}
        if not required_cols.issubset(df.columns):
            raise ValueError(f"Missing required columns: {required_cols - set(df.columns)}")

        G = nx.Graph()
        for provider_id, group in df.groupby('provider_id'):
            patients = group['patient_id'].unique()
            for i, p1 in enumerate(patients):
                for p2 in patients[i + 1:]:
                    if G.has_edge(p1, p2):
                        G[p1][p2]['weight'] += 1
                    else:
                        G.add_edge(p1, p2, weight=1)

        context['total_nodes'] = G.number_of_nodes()
        context['total_edges'] = G.number_of_edges()

        from networkx.algorithms.community import greedy_modularity_communities
        communities = list(greedy_modularity_communities(G))
        suspicious = [sorted(list(c)) for c in communities if len(c) > settings.FRAUD_COMMUNITY_SIZE_THRESHOLD]

        context['num_communities'] = len(communities)
        context['suspicious_communities'] = suspicious
        context['num_suspicious'] = len(suspicious)
        context['message'] = "Model executed successfully. Suspicious communities detected based on community size threshold."

    except FileNotFoundError:
        context['error'] = f"Error: Data file not found at {DATA_PATH}. Please ensure the path is correct."
    except Exception as e:
        context['error'] = f"Error during model execution: {str(e)}"

    return render(request, 'admin_model_execution.html', context)

@never_cache
def admin_covisit_network(request):
    if not request.session.get('is_admin'):
        messages.error(request, "Admin login required.")
        return redirect('admin_login')

    context = {}

    try:
        df = pd.read_csv(DATA_PATH)
        df.columns = df.columns.str.strip().str.lower()

        required_cols = {'provider_id', 'patient_id'}
        if not required_cols.issubset(df.columns):
            raise ValueError("Required columns not found.")

        G = nx.Graph()
        for provider_id, group in df.groupby('provider_id'):
            patients = group['patient_id'].unique()
            for i, p1 in enumerate(patients):
                for p2 in patients[i + 1:]:
                    if G.has_edge(p1, p2):
                        G[p1][p2]['weight'] += 1
                    else:
                        G.add_edge(p1, p2, weight=1)

        plt.figure(figsize=(10, 10))
        pos = nx.spring_layout(G, seed=42)
        nx.draw(G, pos, node_size=30, edge_color='gray', with_labels=False)
        plt.title("Covisit Network")
        image_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
        os.makedirs(image_dir, exist_ok=True) # Ensure directory exists
        image_path = os.path.join(image_dir, 'network.png')
        plt.savefig(image_path)
        plt.close()

        context['network_image'] = 'network.png' # This assumes staticfiles are configured to find network.png
        context['network_info'] = {
            'total_nodes': G.number_of_nodes(),
            'total_edges': G.number_of_edges()
        }

        from networkx.algorithms.community import greedy_modularity_communities
        communities = list(greedy_modularity_communities(G))
        suspicious = [sorted(list(c)) for c in communities if len(c) > settings.FRAUD_COMMUNITY_SIZE_THRESHOLD]
        context['suspicious_communities'] = suspicious
        context['num_suspicious'] = len(suspicious)

    except FileNotFoundError:
        messages.error(request, f"Error: Data file not found at {DATA_PATH}. Please ensure the path is correct.")
        return redirect('admin_home')
    except Exception as e:
        messages.error(request, f"Error visualizing network: {str(e)}")
        return redirect('admin_home')

    return render(request, 'admin_covisit_network.html', context)

@never_cache
def admin_fraud_report(request):
    if not request.session.get('is_admin'):
        messages.error(request, "Admin login required.")
        return redirect('admin_login')

    context = {}

    try:
        df = pd.read_csv(DATA_PATH)
        df.columns = df.columns.str.strip().str.lower()

        required_cols = {'provider_id', 'patient_id'}
        if not required_cols.issubset(df.columns):
            raise ValueError(f"Missing required columns: {required_cols - set(df.columns)}")

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
        suspicious = [sorted(list(c)) for c in communities if len(c) > settings.FRAUD_COMMUNITY_SIZE_THRESHOLD]

        reports = []
        for community in suspicious:
            # Filter original DataFrame for claims involving patients in this suspicious community
            community_claims_df = df[df['patient_id'].isin(community)]
            reports.append({
                'community_size': len(community),
                'patients_in_community': sorted(community), # Optional: list patient IDs
                'claims': community_claims_df.to_dict(orient='records')
            })

        context = {
            'total_nodes': G.number_of_nodes(),
            'total_edges': G.number_of_edges(),
            'num_communities': len(communities),
            'suspicious_communities': reports, # Pass reports directly
            'num_suspicious': len(suspicious),
        }

    except FileNotFoundError:
        context = {'error': f"Error: Data file not found at {DATA_PATH}. Please ensure the path is correct."}
    except Exception as e:
        context = {'error': f"Error generating report: {str(e)}"}

    return render(request, 'admin_fraud_report.html', context)

# --- Consolidated & Updated Fraud Check View ---
# This view now calls the new network-based fraud assessment helper
@never_cache
def assess_claim_status(request, claim_id):
    if not request.session.get('is_admin'):
        messages.error(request, "Admin login required.")
        return redirect('admin_login')

    try:
        claim = get_object_or_404(Claim, id=claim_id)

        # Call the new network-based fraud assessment helper
        fraud_score, fraud_notes = calculate_fraud_score_and_notes(claim)

        # Apply final decision based on total score threshold
        # You might want to adjust FRAUD_TOTAL_SCORE_THRESHOLD in settings.py
        # since you've removed one of the checks (Paid Amount).
        if fraud_score >= settings.FRAUD_TOTAL_SCORE_THRESHOLD:
            claim.status = "Rejected"
            claim.notes = f"Fraud Score: {fraud_score} (Threshold: {settings.FRAUD_TOTAL_SCORE_THRESHOLD}). Reasons: " + "; ".join(fraud_notes)
        else:
            claim.status = "Accepted"
            claim.notes = f"Fraud Score: {fraud_score} (Threshold: {settings.FRAUD_TOTAL_SCORE_THRESHOLD}). Reasons: " + "; ".join(fraud_notes) if fraud_notes else "No suspicious indicators detected by rules."

        claim.save()
        messages.success(request, f"Fraud assessment completed for Claim ID: {claim.claim_id}. Status: {claim.status}. Score: {fraud_score}.")

    except Exception as e:
        messages.error(request, f"An unexpected error occurred during fraud assessment for Claim ID {claim_id}: {str(e)}")
        # If an error prevents assessment, set status to pending or an error state if appropriate
        try:
            claim = get_object_or_404(Claim, id=claim_id) # Re-fetch in case of initial error
            claim.status = "Error during assessment"
            claim.notes = f"Assessment failed: {str(e)}"
            claim.save()
        except:
            pass # If claim itself couldn't be found/saved, just log and redirect

    return redirect('admin_claim_list')

@never_cache
def admin_logout(request):
    request.session.flush()
    messages.success(request, "Admin logged out successfully.")
    return redirect('admin_login')