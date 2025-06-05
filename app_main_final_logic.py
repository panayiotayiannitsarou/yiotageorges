
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import math

SECURITY_CODE = "katanomi2025"

def has_conflict(student, target_class):
    for s in target_class:
        if s['name'] in student['conflicts'] or student['name'] in s['conflicts']:
            return True
    return False

def is_mutual(friend, student, students_dict):
    return friend in students_dict and student['name'] in students_dict[friend]['friends']

def assign_students_full_logic(students):
    num_classes = math.ceil(len(students) / 25)
    classes = [[] for _ in range(num_classes)]
    students_dict = {s['name']: s for s in students}

    # Βήμα 1: Παιδιά Εκπαιδευτικών
    teacher_children = [s for s in students if s['is_teacher_child']]
    for i, s in enumerate(teacher_children):
        target_class = classes[i % num_classes]
        if not has_conflict(s, target_class):
            target_class.append(s)
            s['assigned'] = True

    # Βήμα 2: Φίλοι παιδιών εκπαιδευτικών
    for cl in classes:
        for s in cl.copy():
            for f in s['friends']:
                if f in students_dict:
                    friend = students_dict[f]
                    if not friend['is_teacher_child'] and not friend.get('assigned') and is_mutual(f, s, students_dict):
                        if not has_conflict(friend, cl):
                            cl.append(friend)
                            friend['assigned'] = True

    # Βήμα 3: Ζωηροί μαθητές
    lively_students = [s for s in students if s['is_lively'] and not s.get('assigned')]
    for s in lively_students:
        possible_classes = [cl for cl in classes if sum(1 for x in cl if x['is_lively']) < 2 and not has_conflict(s, cl)]
        if possible_classes:
            target_class = min(possible_classes, key=lambda cl: len(cl))
            target_class.append(s)
            s['assigned'] = True

    # Βήμα 4: Μαθητές με ιδιαιτερότητες
    special_students = [s for s in students if s['is_special'] and not s.get('assigned')]
    for s in special_students:
        possible_classes = [cl for cl in classes if not has_conflict(s, cl)]
        if possible_classes:
            target_class = min(possible_classes, key=lambda cl: sum(1 for x in cl if x['is_lively']))
            target_class.append(s)
            s['assigned'] = True

    # Βήμα 5: Μαθητές με χαμηλή γλωσσική επάρκεια
    language_students = [s for s in students if s['is_language_support'] and not s.get('assigned')]
    for s in language_students:
        placed = False
        for f in s['friends']:
            if f in students_dict and students_dict[f].get('assigned'):
                for cl in classes:
                    if students_dict[f] in cl and len(cl) < 25 and not has_conflict(s, cl):
                        cl.append(s)
                        s['assigned'] = True
                        placed = True
                        break
            if placed:
                break
        if not s.get('assigned'):
            possible_classes = [cl for cl in classes if not has_conflict(s, cl)]
            if possible_classes:
                target_class = min(possible_classes, key=lambda cl: sum(1 for x in cl if x['is_language_support']))
                target_class.append(s)
                s['assigned'] = True

    # Βήμα 6: Μαθητές με ικανοποιητική μαθησιακή ικανότητα
    good_students = [s for s in students if s['is_good_learning'] and not s.get('assigned')]
    for s in good_students:
        possible_classes = [cl for cl in classes if not has_conflict(s, cl)]
        if possible_classes:
            target_class = min(possible_classes, key=lambda cl: len(cl))
            target_class.append(s)
            s['assigned'] = True

    # Βήμα 7: Υπόλοιποι μαθητές με αμοιβαίες φιλίες
    unassigned = [s for s in students if not s.get('assigned')]
    for s in unassigned:
        if not s.get('assigned'):
            group = [s]
            for f in s['friends']:
                if f in students_dict and is_mutual(f, s, students_dict):
                    friend = students_dict[f]
                    if not friend.get('assigned'):
                        group.append(friend)
            if len(group) <= 3:
                possible_classes = [cl for cl in classes if len(cl) + len(group) <= 25 and all(not has_conflict(member, cl) for member in group)]
                if possible_classes:
                    target_class = min(possible_classes, key=lambda cl: len(cl))
                    for member in group:
                        target_class.append(member)
                        member['assigned'] = True

    # Βήμα 8: Υπόλοιποι μαθητές χωρίς φιλίες
    unassigned = [s for s in students if not s.get('assigned')]
    for s in unassigned:
        possible_classes = [cl for cl in classes if not has_conflict(s, cl)]
        if possible_classes:
            target_class = min(possible_classes, key=lambda cl: len(cl))
            target_class.append(s)
            s['assigned'] = True

    # Τελικό Βήμα: Ισορροπία πληθυσμού (μέγιστη διαφορά 1 μαθητή)
    balanced = False
    while not balanced:
        sizes = [len(cl) for cl in classes]
        max_size, min_size = max(sizes), min(sizes)
        if max_size - min_size <= 1:
            balanced = True
        else:
            donor = max(classes, key=lambda cl: len(cl))
            receiver = min(classes, key=lambda cl: len(cl))
            student_to_move = next((s for s in donor if not has_conflict(s, receiver)), None)
            if student_to_move:
                donor.remove(student_to_move)
                receiver.append(student_to_move)

    return classes

def calculate_stats(classes):
    stats = []
    for idx, cl in enumerate(classes, start=1):
        boys = sum(1 for s in cl if s['gender'] == "Male")
        girls = sum(1 for s in cl if s['gender'] == "Female")
        teacher_children = sum(1 for s in cl if s['is_teacher_child'])
        lively = sum(1 for s in cl if s['is_lively'])
        special = sum(1 for s in cl if s['is_special'])
        language_support = sum(1 for s in cl if s['is_language_support'])
        good_learning = sum(1 for s in cl if s['is_good_learning'])
        stats.append({
            "Τμήμα": f"Τμήμα {idx}",
            "Αγόρια": boys,
            "Κορίτσια": girls,
            "Παιδιά Εκπαιδευτικών": teacher_children,
            "Ζωηροί": lively,
            "Ιδιαιτερότητες": special,
            "Χαμηλή Γλωσσική Επάρκεια": language_support,
            "Καλή Μαθησιακή Ικανότητα": good_learning
        })
    return pd.DataFrame(stats)

st.set_page_config(page_title="Κατανομή Μαθητών", layout="wide")
st.title("🧮 Εργαλείο Κατανομής Μαθητών")

accept_terms = st.checkbox("⚠️ Απαγορεύεται η χρήση χωρίς ρητή γραπτή άδεια από την δημιουργό.")
password = st.text_input("Κωδικός Πρόσβασης", type="password")

if accept_terms and password == SECURITY_CODE:
    uploaded_file = st.file_uploader("📥 Ανέβασε το αρχείο Excel με τους μαθητές", type=["xlsx"])
    if uploaded_file:
        df = pd.read_excel(uploaded_file, engine='openpyxl')
        st.success("✅ Το αρχείο ανέβηκε και διαβάστηκε επιτυχώς.")
        st.dataframe(df)

        if st.button("🔘 Ξεκίνα την Κατανομή"):
            st.info("⚙️ Εκτελείται η κατανομή...")
            students = []
            for idx, row in df.iterrows():
                students.append({
                    "id": idx + 1,
                    "name": row['Όνομα'],
                    "gender": "Male" if row['Φύλο'] == "Α" else "Female",
                    "is_teacher_child": row['Παιδί Εκπαιδευτικού'] == "Ν",
                    "is_lively": row['Ζωηρός'] == "Ν",
                    "is_special": row['Ιδιαιτερότητα'] == "Ν",
                    "is_language_support": row['Καλή γνώση Ελληνικών'] == "Ν",
                    "is_good_learning": row['Ικανοποιητική μαθησιακή ικανοτητα'] == "Ο",
                    "friends": [f.strip() for f in str(row['Φίλος/Φίλη']).split(",") if pd.notna(row['Φίλος/Φίλη'])],
                    "conflicts": [c.strip() for c in str(row['Συγκρούσεις']).split(",") if pd.notna(row['Συγκρούσεις'])]
                })

            classes = assign_students_full_logic(students)
            st.success("✅ Η κατανομή ολοκληρώθηκε!")

            for idx, cl in enumerate(classes, start=1):
                st.markdown(f"**Τμήμα {idx}**")
                st.write(", ".join(s['name'] for s in cl))

            if st.button("📊 Εμφάνιση Στατιστικών"):
                df_stats = calculate_stats(classes)
                st.dataframe(df_stats)
                df_stats.set_index("Τμήμα")[["Αγόρια", "Κορίτσια", "Παιδιά Εκπαιδευτικών", "Ζωηροί",
                                              "Ιδιαιτερότητες", "Χαμηλή Γλωσσική Επάρκεια",
                                              "Καλή Μαθησιακή Ικανότητα"]].plot(kind="bar")
                plt.ylabel("Πλήθος")
                plt.title("Στατιστικά ανά Τμήμα")
                st.pyplot(plt)

st.markdown("""
<style>
.logo-container {
    position: fixed;
    bottom: 10px;
    right: 10px;
    opacity: 0.5;
}
</style>
<div class='logo-container'>
    <img src='logo.png' width='100'>
</div>
\"", unsafe_allow_html=True)
