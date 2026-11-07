# Approved visual references

The screenshots in this directory are the design source for implementation. They are not webpage backgrounds or substitutes for functioning HTML.

Priority: `home-final.png` defines the latest homepage composition, OTC placement and industry-logo strip. The public pages 01–08 and 09–16 sheets define the individual public layouts. The admin screens 01–08 and 09–16 sheets define the private management layouts. Earlier overview and flow images preserve the full design history. `page-map.ta.md` describes the agreed content and click destinations.

## Public screen mapping

01 `/` — hero, services, OTC, updates, courses, industry logos, footer.
02 `/pages/company` — founder, mission, vision, expertise.
03 `/pages/service` — eight-service catalogue.
04 `/read/<service-id>` — scope, process, deliverables, FAQ.
05 `/other-services` — OTC card and ticker.
06 `/pages/course` — catalogue, search/category/level filters.
07 `/read/<course-id>` — curriculum and learning outcomes.
08 `/training-enquiry?course=...` — course enquiry form.
09 `/pages/tool` — searchable tool catalogue.
10 `/read/<tool-id>` — features, use cases and documentation.
11 `/pages/threat` — advisory catalogue.
12 `/read/<advisory-id>` — summary, affected systems, impact, mitigation, references.
13 `/pages/resource` — blog/research/download collections.
14 `/read/<article-id>` — article/resource detail.
15 `/pages/news` — published news catalogue.
16 `/contact` — enquiry form and company contact details.

## Private screen mapping

01 `/admin/login`; 02 `/admin/dashboard`; 03 `/admin/control/pages`; 04 `/admin/control/ticker`; 05 `/admin/control/services`; 06 `/admin/control/brand`; 07 `/admin/control/news`; 08 `/admin/studio/edit/<id>`; 09 `/admin/control/imports`; 10 `/admin/control/sources`; 11 `/admin/control/tools`; 12 `/admin/control/courses`; 13 `/admin/control/resources`; 14 `/admin/enquiries`; 15 `/admin/control/motion`; 16 `/admin/control/publish`.

Draft/edit/preview/publish, visibility, search, source import, media validation and content permissions use functioning backend routes. The review sheets also propose capabilities beyond the current implementation: drag-and-drop arbitrary page sections, nested lessons/assignments with file management, PDF replacement/version management, event registration, scheduled publication, granular publishing roles, and separately configurable animation effects. These still require implementation; their presence in a reference image is not a claim that they are finished.

The reviewed 2026 CISA snapshot supplies the initial news selection; subsequent imports remain private until reviewed and published. No illustrative attack story from the design sheet is silently represented as verified current news. Course cards are previews pending owner-provided course details.

New attachment review: design/review-2026-11-07/references.json maps all 14 supplied attachments to 8 unique reference images. OTC now sits below Courses in a 15px-title secondary row; its running text remains. The reference methodology strip and authenticated trash/revision recovery controls are implemented. Restoring a trashed item keeps it hidden, and restoring a revision updates only the private draft.
