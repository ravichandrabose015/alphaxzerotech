# AlphaX ZeroTech — Page-by-page design review

இவை programming தொடங்குவதற்கு முன் பார்க்க வேண்டிய proposed page designs. Public website மற்றும் private admin தனித்தனியாகக் காட்டப்பட்டுள்ளன. Content samples demo; images இயங்கும் website அல்ல.

## Image 1 — Public website pages 01–08

| எண் | Page | என்ன content இருக்கும்? | எதை அழுத்தினால் எங்கு செல்லும்? |
|---|---|---|---|
| 01 | Home | Logo/menu, running announcement, shield hero, services, course/update previews | Services → 03; Courses → 06; Contact → 16 |
| 02 | Company | Founder, mission, vision, expertise, company introduction | Consultation → 16 |
| 03 | Cybersecurity Services | Web, network, cloud, mobile, API, pentesting, audit, SOC service cards | Service → 04; Other Services → 05 |
| 04 | Service Detail | Overview, scope, process, deliverables, FAQs | Request Audit → 16 |
| 05 | Other Services / OTC | தனியாக OTC service card மற்றும் announcement ticker | Enquire Now → 16; OTC service selected |
| 06 | Courses | Course catalogue, categories, difficulty, search/filter | View Course → 07 |
| 07 | Course Detail | Curriculum, modules, lessons, labs, outcomes | Enquire → 08 |
| 08 | Training Enquiry | Name, email, phone, selected course, message | Submit → confirmation → team follow-up |

OTC exact content:

- Title: **OTC Digital Asset Services**
- Description: **USDT OTC transaction coordination and brokerage support.**
- Button: **Enquire Now**
- Ticker: **USDT OTC Transaction Coordination & Brokerage Support • Contact Us for Enquiries**

OTC என்பது enquiry-only informational section. Payment collection, wallet connection, trading, customer fund handling ஆகியவை இதில் இல்லை.

## Image 2 — Public website pages 09–16

| எண் | Page | என்ன content இருக்கும்? | அடுத்து என்ன திறக்கும்? |
|---|---|---|---|
| 09 | Security Tools | Search/filter, tool catalogue cards | View Tool → 10 |
| 10 | Tool Detail | Features, use cases, screenshots, documentation, access information | Request Access → 16 |
| 11 | Threat Intelligence | Reviewed research/advisory cards; source/date; categories | Read Advisory → 12 |
| 12 | Advisory Detail | Summary, affected systems, impact, mitigation, references | Related Service → 04; Enquiry → 16 |
| 13 | Resources | Blog, case studies, guides, downloads | Story → 14; PDF → file download |
| 14 | Article / Case Study | Article body, author/date; context, approach, outcome, related content | Related article அல்லது Contact → 16 |
| 15 | News & Events | Security news, company announcements, events; story/event detail | Read Story; Register Interest → 08 |
| 16 | Contact / Enquiry | Service/course/OTC/tool enquiry, contact preference, public company details | Submit → confirmation → follow-up |

News/event detail presentation image 15-ல் preview ஆக உள்ளது. ஒவ்வொரு article/event-க்கும் தனி URL வழங்க implementation-ல் இந்த templates reuse செய்யப்படும்; அவை எல்லாம் ஒரே permanent content item அல்ல.

## Image 3 — Admin screens 01–08

| எண் | Admin page | Owner என்ன செய்யலாம்? |
|---|---|---|
| 01 | Login | Private administrator sign-in |
| 02 | Dashboard | Draft/review/scheduled/enquiry overview; management shortcuts |
| 03 | Page Builder | Words, headings, images, button links; section add, reorder, hide, remove |
| 04 | Ticker & OTC Settings | Top/section ticker text, speed, pause, visibility; OTC title/description/button; contact destination |
| 05 | Company & Services | Company/team details; services, scope, process, deliverables, FAQs add/edit/hide/trash |
| 06 | Menus & Brand | Menu add/rename/reorder, child menus, links; colours, logo, footer/contact |
| 07 | News Manager | News add/edit, draft/published/scheduled/trash filters, unpublish/remove |
| 08 | News / Article Editor | Title, summary, body, cover, category, source/date; draft, preview, schedule, publish |

## Image 4 — Admin screens 09–16

| எண் | Admin page | Owner என்ன செய்யலாம்? |
|---|---|---|
| 09 | Threat Import Inbox | Imported content review, verify source/date, import/skip, approve |
| 10 | Source Controls | Source enable/pause, refresh, manual sync, duplicates, removed-item suppression |
| 11 | Tools Manager | Tool listing, description, screenshots, documentation, access link add/edit/hide/trash |
| 12 | Courses & Lessons | Courses, modules, lessons, labs, assignments and learning-file management |
| 13 | Resources & Downloads | Blog/case study/event content, images/PDFs upload/replace/version/update/remove |
| 14 | Enquiries | Filter, assign owner, preferred contact, notes, follow-up status, export |
| 15 | Motion Settings | Hero/menu/button effects, ticker speed, pause, reduced motion, mobile intensity |
| 16 | Preview / Publish / History | Desktop/mobile preview, draft/schedule/publish, revisions, trash restore, roles |

## Owner content workflow

Create / Import → Edit → Review → Preview → Publish → Update / Unpublish / Trash → Restore.

External news imports default-ஆக review inbox-க்கு வரும். Admin publish செய்தபின் public listing-ல் வரும். Remove செய்த item அடுத்த refresh-ல் திரும்பாதபடி suppression வைத்திருக்க வேண்டும். Source date, fetched time, update time ஆகியவை தனி fields.

## Motion review

- Menu: click/tap expand; keyboard access.
- Hero: slow shield orbit, mesh/pulse; text stable.
- Buttons: hover/press/loading/success feedback.
- Ticker: slow movement; pause on hover/focus; manual pause.
- Reduced motion: static readable text and restrained transitions.
- Admin: effect/speed/visibility settings; form inputs மற்றும் reading content stable.

## Programming approval boundary

இந்த images configured content, controls மற்றும் page templates-ஐ முன்மொழிகின்றன. அங்கீகரித்தபின் existing Flask project architecture-க்கு ஏற்ப implement செய்யலாம். Images உருவாக்குவதற்காக live website/admin-ல் மாற்றங்கள் செய்யப்படவில்லை. புதிய feature/backend capability சேர்ப்பதற்கு code தேவை; defined content fields-ஐ owner admin-ல் மாற்றலாம்.
