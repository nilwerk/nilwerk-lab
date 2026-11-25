# Posting-day checklist, pack of 24 Nov 2026

For the owner, who posts the LinkedIn text himself. Tick every box on the posting day; if one cannot be ticked, do not post. The Instagram cards wait until the 30- and 90-day chart exists.

Several changes marked "in review" in the draft have been merged since it was written, so the draft's labels and some numbers are stale until they are recounted.

## 1. Recount the labels ("on main" or "in review")
- [ ] Fetch the main branch first (`git fetch origin`), then check each item below against `origin/main`, not against memory or the draft.
- [ ] For every item: is the code on main? Use `git ls-tree -r origin/main --name-only` for the files and `git merge-base --is-ancestor <commit> origin/main` (exit code 0 means on main). A merged label on a branch is not proof; the ancestry check is.
- [ ] Connect-your-AI screen (draft says "in review", the 475-test count): the screen is now merged. Change the label to "on main" and recount the app tests from a fresh CI run on main; the number 475 came from a local run and must not be reused unchecked.
- [ ] Boot-loop guard (draft says "in review"): check merge state, then the label. The numbers (433 checks, 46 of 46 deliberate bugs caught) are only valid for the version that was tested; re-read them from the latest run.
- [ ] Watering rule (draft says "in review", "main still counts only rises above 10"): check the main branch code for the 10-point rule ("10 or more") and the 2-hour gap. If merged, delete the sentence about main still counting only rises above 10 and re-read the test counts (7, 13, 6 of 6).
- [ ] Health check for the bench (draft says "in review, not run on the Pi"): check merge state. Merged is not the same as "run on the Pi": say "not run on the Pi" until a bench run with a log shows it.
- [ ] Premium dashboard and analytics endpoint (draft says "on main"): confirm they are still on main.
- [ ] App test count on main (draft: 443): take the count from the latest CI job log on main, not from the green tick. The count has probably moved; replace it in both languages and on card 5.
- [ ] Endpoint tests (draft: 13): re-read from the latest run.
- [ ] Update every changed label and number in all six places: English post, German post, both "for engineers" lists, both card 5 texts, and the claim table.

## 2. Wording that must stay true after the recount
- [ ] "Nothing ran on a phone or against a live backend" stays only if still true; the bench did install the app on a phone, so keep the sentence limited to the app screens, or reword it.
- [ ] The key list reload: the screen reloads the key list from the server after a lost or unusable reply when creating a key (and after "not found" when revoking). If the code changes, reword.
- [ ] The key create and revoke server function: confirm on main whether it exists. If it still does not exist, keep "mocked backend only".
- [ ] No "faster", "first", "best" or other superlatives; no time figure unless a measured total exists in a daily report.
- [ ] The human-review line is in both languages: "AI agents, led and reviewed by humans" and "KI-Agenten, geleitet und geprüft von Menschen".

## 3. Bench status before any bench sentence
- [ ] Open the latest bench pipeline run and read each step. State today's real result: which steps are green and which are red.
- [ ] If the app-flow step is now green, the sentences "one step stayed red", "partial success" and the red step on card 5 must be rewritten, not just edited; the title card stays only if the three catches still hold.
- [ ] If the run is red for a different reason, name that reason from the log, not the one from 24 Nov.
- [ ] Say "run on main" only for a run on the main branch, and give the date of that run.

## 4. Forbidden-text check
- [ ] Re-run the grep on the final text (it must print nothing):
  `grep -nE '#[0-9]+|[0-9]\.[A-Z]+[0-9]*|A-[0-9]+|Arsany|Nora|Theo|Ines|Kai|Mira|Leo|Sana|Emil|Yara|Peter|Max|Poppy|\.md|\.tsx?|/projects/|https?://' <the text file>`
- [ ] Read the text once more for names of people, customers, prices, secrets and private links. The claim table is for reviewers and does not go into the post.

## 5. Images and labels
- [ ] No image is built yet. If one is added: code-generated charts, renders and text cards are not AI imagery; a picture made by an AI model is. Mark any AI-made image as "AI-generated" in the text and set the platform's AI flag.
- [ ] No real photo of the bench is used unless the person who built it has agreed to its public use.
- [ ] Alt text exists for every image.

## 6. Posting
- [ ] The owner has read the German text himself (native check) and approved it.
- [ ] The owner posts it himself, from the company page, at a time he chooses. Nothing is scheduled by an agent.
- [ ] After posting, note the date, the final numbers and the labels used, so the next pack can start from them.
