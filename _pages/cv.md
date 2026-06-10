---
layout: page
permalink: /cv/
title: CV
nav: true
nav_order: 3
description: Curriculum vitae of Jehyeon Shin. Auto-generated from CV master data.
---

<!--
  이 페이지는 _data/cv_sections.yml (자동 생성) 를 렌더링합니다.
  내용 수정은 OneDrive 의 information.xlsx / _pipeline/profile.yml 에서 하세요.
  레이아웃/스타일만 이 파일에서 직접 수정합니다.
-->

<style>
  .cv-toolbar { margin: 0 0 1.6rem; }
  .cv-btn {
    display: inline-block; padding: .35rem .9rem; border-radius: 6px;
    border: 1px solid var(--global-divider-color, #e0e0e0);
    color: var(--global-theme-color, #b509ac); text-decoration: none; font-size: .95rem;
  }
  .cv-btn:hover { background: var(--global-theme-color, #b509ac); color: #fff; }
  .cv-section { margin: 0 0 1.6rem; }
  .cv-section h2 { margin-bottom: .2rem; }
  .cv-note { font-size: .9rem; opacity: .7; margin: 0 0 .6rem; }
  .cv-item { display: flex; gap: 1rem; margin-bottom: .65rem; line-height: 1.45; }
  .cv-date { flex: 0 0 9rem; opacity: .7; font-size: .9rem; padding-top: .05rem; }
  .cv-body { flex: 1 1 auto; }
  .cv-sub  { opacity: .75; font-size: .92rem; }
  @media (max-width: 600px) {
    .cv-item { flex-direction: column; gap: .1rem; }
    .cv-date { flex-basis: auto; }
  }
</style>

<div class="cv-toolbar">
  <a class="cv-btn" href="{{ '/assets/pdf/cv.pdf' | relative_url }}" target="_blank" rel="noopener">📄 Download PDF CV</a>
  <a class="cv-btn" href="{{ '/publications/' | relative_url }}">📚 Publications</a>
</div>

{% for section in site.data.cv_sections.sections %}
<div class="cv-section">
  <h2>{{ section.title }}</h2>
  {% if section.note %}<p class="cv-note">{{ section.note }}</p>{% endif %}
  {% for item in section.items %}
  <div class="cv-item">
    {% if item.date %}<div class="cv-date">{{ item.date }}</div>{% endif %}
    <div class="cv-body">
      {% if item.main %}<div class="cv-main">{{ item.main | markdownify | remove: '<p>' | remove: '</p>' | strip_newlines }}</div>{% endif %}
      {% if item.sub %}<div class="cv-sub">{{ item.sub | markdownify | remove: '<p>' | remove: '</p>' | strip_newlines }}</div>{% endif %}
    </div>
  </div>
  {% endfor %}
</div>
{% endfor %}
