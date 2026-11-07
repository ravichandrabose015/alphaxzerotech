# Verification — 7 November 2026

- Automated suite: **17 passed**. Covers enquiry/admin workflow; draft isolation; publishing, hiding and removal; stale revision rejection; anonymous/editor authorization; CSRF; unsafe URLs; revoked sessions; current-password checks; setup protection; OTC preselection; public pages; spoofed forwarding headers; image decoding and draft image privacy; menu URL validation; download visibility; imported news deduplication and deletion suppression.
- Requirements audit: **no known vulnerabilities found** after upgrading Pillow to the fixed 13.x series. This is an advisory database check, not proof that every vulnerability is absent.
- Python compilation and Git whitespace checks passed.
- Browser: homepage and OTC enquiry checked; mobile menu opens; no horizontal overflow in observed desktop/mobile layouts; visible homepage image assets loaded. OTC service is automatically selected in the form. Pause/reduced-motion behavior is implemented in CSS/JS; assistive-technology testing is still outstanding.
- Live CISA import into isolated preview database: three entries imported as private drafts. No automatic publication.
- Production database and original PostgreSQL marketplace have not been modified or integration-tested. No production launch has occurred.
- Render service identification, authenticated dashboard access, existing data backup/migration and production smoke checks remain required for launch. GitHub source access is available.

The public preview uses isolated local data. No production credentials or customer data are included in this branch. Logo source attribution is retained in `static/images/industry/logo-sources.md`.

Reference correction: collected all available approved images in design/approved. Added specialized public templates, compact reference-based styling, source-derived hero artwork, SVG service/course icons and twelve dedicated admin management views. Automated checks render each public page family and each private management view. Visual comparison is in progress; the remaining proposed capabilities are listed in design/approved/README.md.

Compact/motion refinement: 20 tests pass. Top announcement removed from public layout; OTC section ticker retains slow CSS motion without a surrounding box. Browser checks at 1280px and 390px showed no horizontal overflow or broken visible images. Desktop homepage H1 measured 46.08px; mobile catalogue H1 measured 29px. Course image backgrounds measured `none`, with three distinct SVG assets and `object-float` animation. Browser news catalogue contained ten entries. Added eleven original SVG illustrations and a bounded 30fps ambient canvas; reduced-motion and hidden-page states stop canvas animation.

Latest attachment review: 14 attachments deduplicated to 8 visual references. OTC moved below Courses, with a 15px desktop title and observed card height 62.6px at 1280px; its enquiry link and section ticker remain. Added the reference methodology/featured-learning strip and navigation icons. Added owner-only, CSRF-protected trash recovery, unpublishing and revision-to-draft recovery with optimistic concurrency checks. Automated suite: 23 passed. Browser verified authenticated access to the recovery screen. Prototype features still outstanding remain listed in design/approved/README.md.
