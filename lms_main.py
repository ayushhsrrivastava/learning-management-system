import sqlite3
import os
import json
import uuid
from flask import Flask, render_template_string, request, session, redirect, url_for, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime

# ==========================================
# CONFIGURATION & SETUP
# ==========================================

app = Flask(__name__)
app.secret_key = 'super_secret_lms_key_change_in_production'
DB_NAME = 'lms_database.db'

# ==========================================
# MASTER TEMPLATE SYSTEM
# ==========================================

MASTER_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Athena LMS</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        body { font-family: 'Inter', sans-serif; }
        .custom-scrollbar::-webkit-scrollbar { width: 4px; }
        .custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
        .custom-scrollbar::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 10px; }
        
        .curriculum-content { max-height: 0; overflow: hidden; transition: max-height 0.3s ease-out; }
        .curriculum-content.expanded { max-height: 1000px; transition: max-height 0.5s ease-in; }
        .chevron-icon { transition: transform 0.3s ease; }
        .chevron-icon.rotated { transform: rotate(180deg); }
        .tab-content { display: none; }
        .tab-content.active { display: block; }

        #search-results-dropdown {
            opacity: 0;
            transform: translateY(-10px);
            pointer-events: none;
            transition: all 0.2s ease;
            z-index: 100;
        }
        #search-results-dropdown.visible {
            opacity: 1;
            transform: translateY(0);
            pointer-events: auto;
        }
    </style>
</head>
<body class="bg-gray-50 text-gray-800">

    {% if session.get('user_id') %}
    <div class="flex h-screen overflow-hidden">
        <!-- Sidebar -->
        <aside class="w-64 bg-slate-900 text-white flex-shrink-0 hidden md:flex flex-col">
            <div class="p-6 flex items-center gap-3 border-b border-slate-700">
                <i class="fa-solid fa-graduation-cap text-2xl text-indigo-400"></i>
                <span class="text-xl font-bold tracking-wide">Athena LMS</span>
            </div>
            <nav class="flex-1 px-4 py-6 space-y-2">
                <a href="{{ url_for('dashboard') }}" class="flex items-center gap-3 px-4 py-3 rounded-lg hover:bg-slate-800 transition {% if active_page == 'dashboard' %}bg-indigo-600 text-white{% else %}text-gray-400{% endif %}">
                    <i class="fa-solid fa-chart-pie w-5"></i> Dashboard
                </a>
                <a href="{{ url_for('explore') }}" class="flex items-center gap-3 px-4 py-3 rounded-lg hover:bg-slate-800 transition {% if active_page == 'explore' %}bg-indigo-600 text-white{% else %}text-gray-400{% endif %}">
                    <i class="fa-solid fa-compass w-5"></i> Explore
                </a>
                <a href="{{ url_for('my_courses') }}" class="flex items-center gap-3 px-4 py-3 rounded-lg hover:bg-slate-800 transition {% if active_page == 'courses' or active_page == 'view_course' %}bg-indigo-600 text-white{% else %}text-gray-400{% endif %}">
                    <i class="fa-solid fa-book-open w-5"></i> My Courses
                </a>
                <a href="{{ url_for('certificates') }}" class="flex items-center gap-3 px-4 py-3 rounded-lg hover:bg-slate-800 transition {% if active_page == 'certificates' %}bg-indigo-600 text-white{% else %}text-gray-400{% endif %}">
                    <i class="fa-solid fa-certificate w-5"></i> My Certificates
                </a>
                <a href="{{ url_for('support') }}" class="flex items-center gap-3 px-4 py-3 rounded-lg hover:bg-slate-800 transition {% if active_page == 'support' %}bg-indigo-600 text-white{% else %}text-gray-400{% endif %}">
                    <i class="fa-solid fa-headset w-5"></i> Help & Support
                </a>
            </nav>
            <div class="p-4 border-t border-slate-700">
                <div class="flex items-center gap-3 mb-4">
                    <div class="w-10 h-10 rounded-full bg-indigo-500 flex items-center justify-center text-white font-bold">
                        {{ session.get('name', 'U')[0] }}
                    </div>
                    <div>
                        <p class="text-sm font-medium">{{ session.get('name') }}</p>
                        <p class="text-xs text-gray-400">Student</p>
                    </div>
                </div>
                <a href="{{ url_for('logout') }}" class="block w-full text-center py-2 text-sm text-red-400 hover:text-red-300">
                    <i class="fa-solid fa-arrow-right-from-bracket"></i> Logout
                </a>
            </div>
        </aside>

        <div class="flex-1 flex flex-col h-full overflow-hidden">
            <header class="h-16 bg-white border-b flex items-center justify-between px-6 shadow-sm z-50">
                <h2 class="text-lg font-semibold text-gray-700 capitalize">{{ active_page | default('Home') | replace('_', ' ') }}</h2>
                <div class="flex-1 max-w-lg mx-6 relative" id="search-container">
                    <form action="{{ url_for('search') }}" method="GET" class="relative">
                        <i class="fa-solid fa-magnifying-glass absolute left-3 top-1/2 -translate-y-1/2 text-gray-400"></i>
                        <input type="text" name="q" id="search-input" autocomplete="off" placeholder="Search courses..." class="w-full pl-10 pr-4 py-2 bg-gray-100 border-none rounded-full text-sm outline-none focus:ring-2 focus:ring-indigo-300 transition-all">
                    </form>
                    <div id="search-results-dropdown" class="absolute top-full left-0 right-0 mt-2 bg-white rounded-xl shadow-2xl border border-gray-100 overflow-hidden max-h-96 overflow-y-auto">
                        <div id="search-results-content" class="p-2"></div>
                    </div>
                </div>
            </header>

            <main class="flex-1 overflow-y-auto {% if active_page != 'view_course' %}p-6{% endif %}">
                {% with messages = get_flashed_messages(with_categories=true) %}
                  {% for category, message in messages %}
                    <div id="toast-message" class="m-4 p-4 rounded-lg shadow-sm border {% if category == 'error' %}bg-red-50 text-red-700 border-red-200{% else %}bg-green-50 text-green-700 border-green-200{% endif %}">
                        {{ message }}
                    </div>
                  {% endfor %}
                {% endwith %}
                
                {% block content_area %}{% endblock %}
            </main>
        </div>
    </div>
    {% else %}
    <div class="min-h-screen flex items-center justify-center bg-gray-100 p-4">
        <div class="bg-white p-8 rounded-2xl shadow-xl w-full max-w-md">
            {% block public_area %}{% endblock %}
        </div>
    </div>
    {% endif %}

    <script>
        const searchInput = document.getElementById('search-input');
        const searchDropdown = document.getElementById('search-results-dropdown');
        const searchContent = document.getElementById('search-results-content');
        let searchTimeout;

        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                clearTimeout(searchTimeout);
                const query = e.target.value.trim();
                if (query.length < 2) { searchDropdown.classList.remove('visible'); return; }

                searchTimeout = setTimeout(async () => {
                    const response = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
                    const results = await response.json();
                    searchContent.innerHTML = '';
                    if (results.length > 0) {
                        results.forEach(item => {
                            const div = document.createElement('div');
                            div.className = "flex items-center gap-3 p-3 hover:bg-indigo-50 cursor-pointer rounded-lg border-b last:border-0 border-gray-50";
                            div.onclick = () => window.location.href = `/course/${item.id}`;
                            div.innerHTML = `
                                <div class="w-8 h-8 bg-indigo-100 rounded flex items-center justify-center text-indigo-600 text-[10px]"><i class="fa-solid fa-play"></i></div>
                                <div class="flex-1 overflow-hidden">
                                    <div class="text-xs font-bold truncate">${item.title}</div>
                                </div>
                            `;
                            searchContent.appendChild(div);
                        });
                    } else {
                        searchContent.innerHTML = '<div class="p-3 text-center text-xs text-gray-400 italic">No matches...</div>';
                    }
                    searchDropdown.classList.add('visible');
                }, 300);
            });
            document.addEventListener('click', (e) => {
                if (!document.getElementById('search-container').contains(e.target)) searchDropdown.classList.remove('visible');
            });
        }

        function toggleSection(sectionId) {
            const content = document.getElementById('content-' + sectionId);
            const icon = document.getElementById('icon-' + sectionId);
            content.classList.toggle('expanded');
            icon.classList.toggle('rotated');
        }

        function playLesson(title) {
            const videoTitle = document.getElementById('active-lesson-title');
            if(videoTitle) videoTitle.innerText = title;
            document.querySelectorAll('.lesson-item').forEach(item => {
                item.classList.remove('bg-indigo-50', 'border-l-4', 'border-indigo-600');
            });
            if(event) event.currentTarget.classList.add('bg-indigo-50', 'border-l-4', 'border-indigo-600');
        }

        function switchTab(tabId) {
            document.querySelectorAll('.tab-btn').forEach(btn => {
                btn.classList.remove('border-indigo-600', 'text-indigo-600');
                btn.classList.add('text-gray-400');
            });
            document.querySelectorAll('.tab-content').forEach(content => { content.classList.remove('active'); });
            event.target.classList.add('border-indigo-600', 'text-indigo-600');
            event.target.classList.remove('text-gray-400');
            document.getElementById('tab-' + tabId).classList.add('active');
        }

        async function downloadCert(course, id, date) {
            const { jsPDF } = window.jspdf;
            const doc = new jsPDF({ orientation: 'landscape' });
            doc.setDrawColor(79, 70, 229);
            doc.setLineWidth(1.5);
            doc.rect(10, 10, 277, 190);
            doc.setLineWidth(0.5);
            doc.rect(12, 12, 273, 186);
            doc.setTextColor(79, 70, 229);
            doc.setFontSize(24);
            doc.setFont("helvetica", "bold");
            doc.text("ATHENA LMS", 148.5, 40, { align: "center" });
            doc.setTextColor(0, 0, 0);
            doc.setFontSize(35);
            doc.text("Certificate of Completion", 148.5, 70, { align: "center" });
            doc.setFontSize(16);
            doc.setFont("helvetica", "normal");
            doc.text("This is to certify that", 148.5, 90, { align: "center" });
            doc.setFontSize(28);
            doc.setFont("helvetica", "bold");
            doc.text("{{ session.get('name') }}", 148.5, 110, { align: "center" });
            doc.setFontSize(16);
            doc.setFont("helvetica", "normal");
            doc.text("has successfully completed the course", 148.5, 130, { align: "center" });
            doc.setFontSize(22);
            doc.setTextColor(79, 70, 229);
            doc.text(course, 148.5, 150, { align: "center" });
            doc.setTextColor(100, 100, 100);
            doc.setFontSize(12);
            doc.text(`Certificate ID: ${id}`, 20, 185);
            doc.text(`Issued Date: ${date}`, 277, 185, { align: "right" });
            doc.save(`${course.replace(/ /g, "_")}_Certificate.pdf`);
        }

        function saveNote() {
            const txt = document.getElementById('note-input').value;
            if(!txt) return;
            const div = document.createElement('div');
            div.className = "p-3 bg-yellow-50 border-l-4 border-yellow-400 text-sm mb-3 rounded-r-lg";
            div.innerHTML = `<p>${txt}</p><p class="text-[10px] text-gray-400 mt-1">Saved just now</p>`;
            document.getElementById('saved-notes').prepend(div);
            document.getElementById('note-input').value = '';
        }
    </script>
</body>
</html>
"""

EXPLORE_FRAG = """
<div class="mb-10">
    <div class="flex flex-wrap items-center gap-3">
        <a href="{{ url_for('explore') }}" class="px-5 py-2 rounded-full text-xs font-bold transition {% if not current_cat %}bg-indigo-600 text-white shadow-lg shadow-indigo-100{% else %}bg-white border text-gray-600 hover:bg-gray-50{% endif %}">All Courses</a>
        <a href="{{ url_for('explore', category='Python') }}" class="px-5 py-2 rounded-full text-xs font-bold transition {% if current_cat == 'Python' %}bg-indigo-600 text-white shadow-lg shadow-indigo-100{% else %}bg-white border text-gray-600 hover:bg-gray-50{% endif %}">Python</a>
        <a href="{{ url_for('explore', category='Design') }}" class="px-5 py-2 rounded-full text-xs font-bold transition {% if current_cat == 'Design' %}bg-indigo-600 text-white shadow-lg shadow-indigo-100{% else %}bg-white border text-gray-600 hover:bg-gray-50{% endif %}">Design</a>
        <a href="{{ url_for('explore', category='Backend') }}" class="px-5 py-2 rounded-full text-xs font-bold transition {% if current_cat == 'Backend' %}bg-indigo-600 text-white shadow-lg shadow-indigo-100{% else %}bg-white border text-gray-600 hover:bg-gray-50{% endif %}">Backend</a>
        <a href="{{ url_for('explore', category='DevOps') }}" class="px-5 py-2 rounded-full text-xs font-bold transition {% if current_cat == 'DevOps' %}bg-indigo-600 text-white shadow-lg shadow-indigo-100{% else %}bg-white border text-gray-600 hover:bg-gray-50{% endif %}">DevOps</a>
        <a href="{{ url_for('explore', category='Management') }}" class="px-5 py-2 rounded-full text-xs font-bold transition {% if current_cat == 'Management' %}bg-indigo-600 text-white shadow-lg shadow-indigo-100{% else %}bg-white border text-gray-600 hover:bg-gray-50{% endif %}">Management</a>
    </div>
</div>

<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
    {% for course in courses %}
    <div class="bg-white p-5 rounded-2xl border flex flex-col h-full hover:shadow-xl transition-all">
        <div class="w-full aspect-video bg-slate-100 rounded-xl mb-4 flex items-center justify-center text-slate-300 text-3xl">
            {% if 'Python' in (course.category or '') %}<i class="fa-brands fa-python text-indigo-400"></i>
            {% elif 'Design' in (course.category or '') %}<i class="fa-solid fa-pen-nib text-indigo-400"></i>
            {% elif 'Backend' in (course.category or '') %}<i class="fa-solid fa-server text-indigo-400"></i>
            {% elif 'DevOps' in (course.category or '') %}<i class="fa-solid fa-infinity text-indigo-400"></i>
            {% else %}<i class="fa-solid fa-layer-group text-indigo-400"></i>{% endif %}
        </div>
        <div class="flex-1">
            <span class="text-[10px] font-black text-indigo-600 uppercase tracking-widest bg-indigo-50 px-2 py-1 rounded">{{ course.category or 'General' }}</span>
            <h4 class="font-black mt-3 mb-2 text-gray-800 leading-tight">{{ course.title }}</h4>
            <p class="text-xs text-gray-500 leading-relaxed">{{ course.description[:120] }}...</p>
        </div>
        <div class="mt-6 pt-4 border-t">
            {% if course.enrolled %}
            <a href="{{ url_for('view_course', course_id=course.id) }}" class="block text-center w-full py-3 bg-indigo-50 text-indigo-600 rounded-xl text-sm font-black transition">Continue Learning</a>
            {% else %}
            <form action="{{ url_for('enroll', course_id=course.id) }}" method="POST">
                <button type="submit" class="w-full py-3 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-sm font-black shadow-lg shadow-indigo-100 transition">Enroll Now</button>
            </form>
            {% endif %}
        </div>
    </div>
    {% endfor %}
</div>
"""

DASHBOARD_FRAG = """
<div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
    <div class="bg-white p-6 rounded-2xl shadow-sm border flex items-center gap-4">
        <div class="w-12 h-12 bg-indigo-50 text-indigo-600 rounded-xl flex items-center justify-center text-xl"><i class="fa-solid fa-spinner"></i></div>
        <div><p class="text-xs font-bold text-gray-400 uppercase tracking-wider">In Progress</p><p class="text-2xl font-black">{{ stats.in_progress }}</p></div>
    </div>
    <div class="bg-white p-6 rounded-2xl shadow-sm border flex items-center gap-4">
        <div class="w-12 h-12 bg-green-50 text-green-600 rounded-xl flex items-center justify-center text-xl"><i class="fa-solid fa-certificate"></i></div>
        <div><p class="text-xs font-bold text-gray-400 uppercase tracking-wider">Certificates</p><p class="text-2xl font-black">{{ stats.completed }}</p></div>
    </div>
    <div class="bg-white p-6 rounded-2xl shadow-sm border flex items-center gap-4">
        <div class="w-12 h-12 bg-orange-50 text-orange-600 rounded-xl flex items-center justify-center text-xl"><i class="fa-solid fa-bolt"></i></div>
        <div><p class="text-xs font-bold text-gray-400 uppercase tracking-wider">Active Status</p><p class="text-2xl font-black">High</p></div>
    </div>
</div>

<h3 class="font-black text-xl mb-6 text-gray-800">Recent Progress</h3>
<div class="grid grid-cols-1 gap-4">
    {% for course in recent_courses %}
    <div class="bg-white p-5 rounded-2xl border flex flex-col md:flex-row md:items-center justify-between gap-4 hover:shadow-md transition">
        <div class="flex items-center gap-4">
            <div class="w-12 h-12 rounded-xl bg-indigo-600 text-white flex items-center justify-center shadow-lg shadow-indigo-100"><i class="fa-solid fa-play text-sm"></i></div>
            <div>
                <span class="font-bold text-gray-800">{{ course.title }}</span>
                <p class="text-[10px] text-gray-400 font-bold uppercase mt-0.5">{{ course.status }}</p>
            </div>
        </div>
        <div class="flex items-center gap-8">
            <div class="w-48">
                <div class="flex justify-between text-[10px] font-bold text-gray-400 mb-1"><span>Completion</span><span>{{ course.progress }}%</span></div>
                <div class="w-full bg-gray-100 h-2 rounded-full overflow-hidden">
                    <div class="bg-indigo-600 h-full transition-all duration-700" style="width: {{ course.progress }}%"></div>
                </div>
            </div>
            <a href="{{ url_for('view_course', course_id=course.course_id) }}" class="px-6 py-2 bg-indigo-50 text-indigo-600 rounded-xl text-xs font-black hover:bg-indigo-600 hover:text-white transition whitespace-nowrap">{% if course.progress >= 100 %}Review{% else %}Resume{% endif %}</a>
        </div>
    </div>
    {% endfor %}
</div>
"""

COURSES_FRAG = """
<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
    {% for course in courses %}
    <div class="bg-white p-5 rounded-2xl border flex flex-col h-full hover:shadow-xl transition-all">
        <div class="w-full aspect-video bg-indigo-50 rounded-xl mb-4 flex items-center justify-center text-indigo-300 text-3xl"><i class="fa-solid fa-clapperboard"></i></div>
        <h4 class="font-black mb-2 text-gray-800 leading-tight">{{ course.title }}</h4>
        <p class="text-xs text-gray-500 flex-1 leading-relaxed">{{ course.description[:120] }}...</p>
        <div class="mt-6 pt-4 border-t">
            <div class="flex justify-between text-[10px] font-black text-gray-400 mb-2 uppercase"><span>{{ course.status }}</span><span>{{ course.progress }}%</span></div>
            <div class="w-full bg-gray-100 h-1.5 rounded-full overflow-hidden mb-6"><div class="bg-indigo-600 h-full" style="width: {{ course.progress }}%"></div></div>
            <a href="{{ url_for('view_course', course_id=course.course_id) }}" class="block text-center w-full py-3 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-sm font-black shadow-lg shadow-indigo-100 transition">View Course</a>
        </div>
    </div>
    {% endfor %}
</div>
"""

VIEW_COURSE_FRAG = """
<div class="flex flex-col lg:flex-row h-full overflow-hidden bg-white">
    <div class="flex-1 flex flex-col h-full overflow-y-auto custom-scrollbar">
        <div class="w-full aspect-video bg-black flex items-center justify-center">
            <video id="main-video" class="w-full h-full" controls poster="https://via.placeholder.com/800x450/000/fff?text=Lesson+Preview">
                <source src="https://storage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4" type="video/mp4">
            </video>
        </div>
        <div class="p-8 max-w-4xl">
            <div class="flex justify-between items-start mb-6">
                <div>
                    <h1 id="active-lesson-title" class="text-3xl font-black text-gray-900 tracking-tight">1.1 Introduction to the Course</h1>
                    <p class="text-sm font-bold text-indigo-500 mt-1 uppercase tracking-wider">{{ course.title }}</p>
                </div>
                <form method="POST" action="{{ url_for('update_progress', course_id=course.course_id) }}">
                    <button type="submit" class="px-8 py-4 bg-green-600 text-white rounded-2xl font-black text-xs hover:bg-green-700 shadow-xl shadow-green-100 transition-all uppercase">
                        <i class="fa-solid fa-check mr-2"></i> Complete Lesson
                    </button>
                </form>
            </div>
            
            <div class="flex gap-8 border-b mb-8 overflow-x-auto">
                <button onclick="switchTab('overview')" class="tab-btn pb-4 border-b-2 border-indigo-600 text-indigo-600 font-black text-xs uppercase tracking-widest">Overview</button>
                <button onclick="switchTab('resources')" class="tab-btn pb-4 text-gray-400 font-black text-xs uppercase tracking-widest hover:text-gray-600">Resources</button>
                <button onclick="switchTab('notes')" class="tab-btn pb-4 text-gray-400 font-black text-xs uppercase tracking-widest hover:text-gray-600">Notes</button>
            </div>
            
            <div id="tab-overview" class="tab-content active text-gray-600 leading-relaxed text-sm">
                <p class="mb-6">{{ course.description }}</p>
            </div>

            <div id="tab-resources" class="tab-content space-y-4">
                <div class="p-5 border rounded-2xl flex items-center justify-between hover:bg-gray-50 transition cursor-pointer group">
                    <div class="flex items-center gap-4">
                        <div class="w-12 h-12 bg-red-50 text-red-500 rounded-xl flex items-center justify-center"><i class="fa-solid fa-file-pdf text-2xl"></i></div>
                        <div><p class="font-black text-sm">Course_Syllabus.pdf</p><p class="text-[10px] font-bold text-gray-400">PDF • 1.2 MB</p></div>
                    </div>
                </div>
            </div>

            <div id="tab-notes" class="tab-content">
                <textarea id="note-input" rows="4" class="w-full p-6 bg-gray-50 border-none rounded-2xl outline-none focus:ring-2 focus:ring-indigo-500 mb-6 text-sm" placeholder="Jot down key takeaways..."></textarea>
                <button onclick="saveNote()" class="px-8 py-3 bg-gray-900 text-white font-black rounded-xl text-xs uppercase">Save Personal Note</button>
                <div id="saved-notes" class="mt-8 space-y-4"></div>
            </div>
        </div>
    </div>

    <aside class="w-full lg:w-96 border-l flex flex-col bg-gray-50 h-full">
        <div class="p-6 border-b bg-white">
            <h3 class="font-black text-gray-800">Curriculum</h3>
            <div class="mt-4">
                <div class="flex justify-between text-[10px] font-black text-gray-400 mb-2 uppercase"><span>Course Progress</span><span>{{ course.progress }}%</span></div>
                <div class="w-full bg-gray-100 h-2 rounded-full overflow-hidden">
                    <div class="bg-indigo-600 h-full transition-all duration-700" style="width: {{ course.progress }}%"></div>
                </div>
            </div>
        </div>
        <div class="flex-1 overflow-y-auto custom-scrollbar">
            {% for section in curriculum %}
            <div class="border-b">
                <button onclick="toggleSection('{{ loop.index }}')" class="w-full px-6 py-5 bg-white text-left flex justify-between items-center hover:bg-gray-50 transition">
                    <span class="font-black text-xs uppercase tracking-wider text-gray-800">{{ section.name }}</span>
                    <i id="icon-{{ loop.index }}" class="fa-solid fa-chevron-down text-[10px] text-gray-400 chevron-icon rotated"></i>
                </button>
                <div id="content-{{ loop.index }}" class="curriculum-content bg-white expanded">
                    {% for lesson in section.lessons %}
                    <div onclick="playLesson('{{ lesson.title }}')" class="lesson-item px-6 py-4 flex items-start gap-4 border-b border-gray-50 hover:bg-indigo-50/50 transition cursor-pointer group">
                        <div class="mt-1">
                            {% if lesson.completed %}<i class="fa-solid fa-circle-check text-green-500"></i>
                            {% else %}<i class="fa-regular fa-circle text-gray-300 group-hover:text-indigo-400"></i>{% endif %}
                        </div>
                        <div class="flex-1">
                            <p class="text-xs font-bold text-gray-700 group-hover:text-indigo-700">{{ lesson.title }}</p>
                        </div>
                    </div>
                    {% endfor %}
                </div>
            </div>
            {% endfor %}
        </div>
    </aside>
</div>
"""

CERTS_FRAG = """
<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
    {% if not certificates %}
    <div class="col-span-full py-20 text-center">
        <div class="w-20 h-20 bg-gray-100 text-gray-300 rounded-full flex items-center justify-center mx-auto mb-4">
            <i class="fa-solid fa-certificate text-3xl"></i>
        </div>
        <h3 class="font-bold text-gray-500">No certificates yet.</h3>
        <p class="text-sm text-gray-400">Complete a course to earn your first one!</p>
    </div>
    {% endif %}
    {% for cert in certificates %}
    <div class="bg-white p-8 rounded-3xl border border-indigo-100 shadow-sm text-center group hover:border-indigo-500 transition-colors">
        <div class="w-20 h-20 bg-indigo-50 text-indigo-600 rounded-full flex items-center justify-center mx-auto mb-6 group-hover:scale-110 transition-transform">
            <i class="fa-solid fa-award text-3xl"></i>
        </div>
        <h3 class="font-black text-lg text-gray-800 mb-1">{{ cert.course_title }}</h3>
        <p class="text-[10px] text-gray-400 font-bold uppercase mb-6 tracking-widest">Issued: {{ cert.date }}</p>
        <button onclick="downloadCert('{{ cert.course_title }}', '{{ cert.id }}', '{{ cert.date }}')" class="w-full py-3 bg-gray-900 hover:bg-indigo-600 text-white rounded-xl text-xs font-black shadow-xl transition-all">Download PDF</button>
    </div>
    {% endfor %}
</div>
"""

SUPPORT_FRAG = """<div class="max-w-2xl mx-auto py-8"><div class="bg-white p-10 rounded-3xl border shadow-xl"><h2 class="text-2xl font-black mb-2">Help & Support</h2><form method="POST" class="space-y-5"><div><label class="text-[10px] font-black text-gray-400 uppercase mb-1 block px-1">Subject</label><input type="text" placeholder="Brief summary" required class="w-full px-4 py-3 border rounded-xl outline-none focus:ring-2 focus:ring-indigo-500 text-sm"></div><div><label class="text-[10px] font-black text-gray-400 uppercase mb-1 block px-1">Detailed Description</label><textarea rows="5" placeholder="Please provide as much detail as possible..." required class="w-full px-4 py-3 border rounded-xl outline-none focus:ring-2 focus:ring-indigo-500 text-sm"></textarea></div><button type="submit" class="w-full py-4 bg-indigo-600 text-white font-black rounded-xl shadow-xl shadow-indigo-100 hover:bg-indigo-700 transition">Submit Request</button></form></div></div>"""
LOGIN_FRAG = """<div class="text-center mb-10"><div class="inline-flex w-16 h-16 bg-indigo-600 text-white rounded-2xl items-center justify-center text-3xl mb-4 shadow-xl shadow-indigo-200"><i class="fa-solid fa-graduation-cap"></i></div><h1 class="text-3xl font-black text-gray-800">Athena LMS</h1></div><form method="POST" action="/login" class="space-y-5"><input type="email" name="email" required placeholder="Email Address" class="w-full px-4 py-4 bg-gray-50 border-none rounded-2xl outline-none focus:ring-2 focus:ring-indigo-500 transition text-sm"><input type="password" name="password" required placeholder="Password" class="w-full px-4 py-4 bg-gray-50 border-none rounded-2xl outline-none focus:ring-2 focus:ring-indigo-500 transition text-sm"><button class="w-full py-4 bg-indigo-600 text-white rounded-2xl font-black shadow-xl shadow-indigo-100 hover:bg-indigo-700 transition">Sign In</button></form><p class="mt-8 text-center text-sm font-medium">New learner? <a href="/signup" class="text-indigo-600 font-black">Create Account</a></p>"""
SIGNUP_FRAG = """<div class="text-center mb-10"><h1 class="text-3xl font-black text-gray-800">Create Account</h1></div><form method="POST" action="/signup" class="space-y-5"><input type="text" name="name" required placeholder="Full Name" class="w-full px-4 py-4 bg-gray-50 border-none rounded-2xl outline-none focus:ring-2 focus:ring-indigo-500 transition text-sm"><input type="email" name="email" required placeholder="Email Address" class="w-full px-4 py-4 bg-gray-50 border-none rounded-2xl outline-none focus:ring-2 focus:ring-indigo-500 transition text-sm"><input type="password" name="password" required placeholder="Password" class="w-full px-4 py-4 bg-gray-50 border-none rounded-2xl outline-none focus:ring-2 focus:ring-indigo-500 transition text-sm"><button class="w-full py-4 bg-indigo-600 text-white rounded-2xl font-black shadow-xl shadow-indigo-100 hover:bg-indigo-700 transition">Get Started</button></form><p class="mt-8 text-center text-sm font-medium">Already registered? <a href="/login" class="text-indigo-600 font-black">Sign In</a></p>"""

# ==========================================
# APP LOGIC
# ==========================================

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    if os.path.exists(DB_NAME):
        os.remove(DB_NAME) 
    
    conn = get_db()
    c = conn.cursor()
    c.execute('CREATE TABLE user (id INTEGER PRIMARY KEY, name TEXT, email TEXT UNIQUE, password TEXT)')
    c.execute('CREATE TABLE course (id INTEGER PRIMARY KEY, title TEXT, description TEXT, type TEXT, category TEXT)')
    c.execute('CREATE TABLE enrollment (id INTEGER PRIMARY KEY, user_id INTEGER, course_id INTEGER, status TEXT, progress INTEGER)')
    c.execute('CREATE TABLE certificate (id TEXT PRIMARY KEY, user_id INTEGER, course_id INTEGER, date_issued TEXT)')
    
    hp = generate_password_hash('password123')
    c.execute("INSERT INTO user (name, email, password) VALUES ('Demo Student', 'user@example.com', ?)", (hp,))
    
    courses = [
        ('Python Masterclass 2024', 'Complete Python from fundamentals to advanced web scraping.', 'Video', 'Python'),
        ('UI/UX Design Systems', 'Learn Figma and design scalable design systems.', 'Video', 'Design'),
        ('Node.js Backend Architecture', 'Architect scalable backend systems with Express.', 'Video', 'Backend'),
        ('Cloud Native DevOps', 'Comprehensive guide to Docker and Kubernetes.', 'Video', 'DevOps'),
        ('Agile Project Management', 'Master scrum and kanban for software teams.', 'Video', 'Management'),
        ('Python for Data Science', 'Numpy, Pandas and Matplotlib for analysis.', 'Video', 'Python')
    ]
    c.executemany("INSERT INTO course (title, description, type, category) VALUES (?,?,?,?)", courses)
    
    # Pre-enroll Demo user
    c.execute("INSERT INTO enrollment (user_id, course_id, status, progress) VALUES (1, 1, 'In Progress', 45)")
    c.execute("INSERT INTO enrollment (user_id, course_id, status, progress) VALUES (1, 2, 'Completed', 100)")
    c.execute("INSERT INTO certificate (id, user_id, course_id, date_issued) VALUES ('CERT-101', 1, 2, '2024-05-10')")
    
    conn.commit()
    conn.close()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session: return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def render_lms(active_page=None, fragment="", **context):
    tpl = MASTER_TEMPLATE.replace('{% block content_area %}{% endblock %}', fragment) if active_page else MASTER_TEMPLATE.replace('{% block public_area %}{% endblock %}', fragment)
    return render_template_string(tpl, active_page=active_page, **context)

@app.route('/')
@login_required
def dashboard():
    conn, uid = get_db(), session['user_id']
    stats = {
        'in_progress': conn.execute("SELECT COUNT(*) FROM enrollment WHERE user_id=? AND status!='Completed'", (uid,)).fetchone()[0],
        'completed': conn.execute("SELECT COUNT(*) FROM enrollment WHERE user_id=? AND status='Completed'", (uid,)).fetchone()[0]
    }
    recent = conn.execute("SELECT c.title, e.progress, e.course_id, e.status FROM enrollment e JOIN course c ON e.course_id=c.id WHERE e.user_id=? LIMIT 4", (uid,)).fetchall()
    return render_lms(active_page='dashboard', fragment=DASHBOARD_FRAG, stats=stats, recent_courses=recent)

@app.route('/explore')
@login_required
def explore():
    conn = get_db()
    cat = request.args.get('category')
    uid = session['user_id']
    
    if cat:
        query = "SELECT c.*, (SELECT 1 FROM enrollment WHERE user_id=? AND course_id=c.id) as enrolled FROM course c WHERE c.category = ?"
        courses = conn.execute(query, (uid, cat)).fetchall()
    else:
        query = "SELECT c.*, (SELECT 1 FROM enrollment WHERE user_id=? AND course_id=c.id) as enrolled FROM course c"
        courses = conn.execute(query, (uid,)).fetchall()
        
    return render_lms(active_page='explore', fragment=EXPLORE_FRAG, courses=courses, current_cat=cat)

@app.route('/enroll/<int:course_id>', methods=['POST'])
@login_required
def enroll(course_id):
    conn = get_db()
    conn.execute("INSERT OR IGNORE INTO enrollment (user_id, course_id, status, progress) VALUES (?, ?, 'In Progress', 0)", (session['user_id'], course_id))
    conn.commit()
    return redirect(url_for('view_course', course_id=course_id))

@app.route('/my-courses')
@login_required
def my_courses():
    conn = get_db()
    courses = conn.execute("SELECT c.id as course_id, c.title, c.description, e.status, e.progress FROM enrollment e JOIN course c ON e.course_id=c.id WHERE e.user_id=?", (session['user_id'],)).fetchall()
    return render_lms(active_page='courses', fragment=COURSES_FRAG, courses=courses)

@app.route('/course/<int:course_id>')
@login_required
def view_course(course_id):
    conn = get_db()
    course = conn.execute("SELECT c.id as course_id, c.title, c.description, e.status, e.progress FROM enrollment e JOIN course c ON e.course_id=c.id WHERE e.user_id=? AND e.course_id=?", (session['user_id'], course_id)).fetchone()
    if not course: return redirect(url_for('explore'))
    prog = course['progress']
    curriculum = [{"name": "Basics", "lessons": [{"title": "Intro", "completed": prog >= 20}, {"title": "Setup", "completed": prog >= 50}]}]
    return render_lms(active_page='view_course', fragment=VIEW_COURSE_FRAG, course=course, curriculum=curriculum)

@app.route('/update-progress/<int:course_id>', methods=['POST'])
@login_required
def update_progress(course_id):
    conn = get_db()
    uid = session['user_id']
    
    # Update progress
    conn.execute("UPDATE enrollment SET progress = MIN(progress + 25, 100) WHERE user_id=? AND course_id=?", (uid, course_id))
    
    # Check if now completed
    row = conn.execute("SELECT progress FROM enrollment WHERE user_id=? AND course_id=?", (uid, course_id)).fetchone()
    if row and row['progress'] >= 100:
        conn.execute("UPDATE enrollment SET status = 'Completed' WHERE user_id=? AND course_id=?", (uid, course_id))
        
        # Check if certificate already exists
        exists = conn.execute("SELECT id FROM certificate WHERE user_id=? AND course_id=?", (uid, course_id)).fetchone()
        if not exists:
            cert_id = f"ATH-{str(uuid.uuid4())[:8].upper()}"
            today = datetime.now().strftime("%Y-%m-%d")
            conn.execute("INSERT INTO certificate (id, user_id, course_id, date_issued) VALUES (?, ?, ?, ?)", (cert_id, uid, course_id, today))
    
    conn.commit()
    return redirect(url_for('view_course', course_id=course_id))

@app.route('/certificates')
@login_required
def certificates():
    conn = get_db()
    certs = conn.execute("""
        SELECT cert.id, c.title as course_title, cert.date_issued as date 
        FROM certificate cert 
        JOIN course c ON cert.course_id = c.id 
        WHERE cert.user_id = ?
    """, (session['user_id'],)).fetchall()
    return render_lms(active_page='certificates', fragment=CERTS_FRAG, certificates=certs)

@app.route('/support', methods=['GET', 'POST'])
@login_required
def support():
    if request.method == 'POST': flash('Ticket sent!', 'success'); return redirect(url_for('dashboard'))
    return render_lms(active_page='support', fragment=SUPPORT_FRAG)

@app.route('/api/search')
@login_required
def api_search():
    q = request.args.get('q', '').lower()
    res = get_db().execute("SELECT id, title FROM course WHERE LOWER(title) LIKE ?", (f'%{q}%',)).fetchall()
    return jsonify([dict(r) for r in res])

@app.route('/search')
@login_required
def search():
    q = request.args.get('q', '')
    res = get_db().execute("SELECT * FROM course WHERE title LIKE ?", (f'%{q}%',)).fetchall()
    return render_lms(active_page='search', fragment=f'<h1 class="text-xl font-bold mb-4">Results for "{q}"</h1>' + EXPLORE_FRAG, courses=res)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u = get_db().execute('SELECT * FROM user WHERE email=?', (request.form['email'],)).fetchone()
        if u and check_password_hash(u['password'], request.form['password']):
            session.update({'user_id': u['id'], 'name': u['name']})
            return redirect(url_for('dashboard'))
    return render_lms(fragment=LOGIN_FRAG)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        conn = get_db()
        hp = generate_password_hash(request.form['password'])
        conn.execute('INSERT INTO user (name, email, password) VALUES (?,?,?)', (request.form['name'], request.form['email'], hp))
        conn.commit()
        return redirect(url_for('login'))
    return render_lms(fragment=SIGNUP_FRAG)

@app.route('/logout')
def logout(): session.clear(); return redirect(url_for('login'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)