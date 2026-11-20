# How to apply these 9 patches to a new folder

The 9 files correspond to the 9 commits from `ab5a0ee` to `591afc5`, in the order of the numbers in their file names.
The paths inside the patches are relative to the project folder (`app.py`, `agents/base.py`, ...), without the `assignment/final_assignment/budget-master/` prefix.

Below, `PATCHES` stands for the path of this folder:

```bash
PATCHES=/Users/ericsong/Course/SWE270P/assignment/final_assignment/patches
```

## 1. Create the folder and initialise a repository

```bash
mkdir -p ~/some-folder/budget-master
cd ~/some-folder/budget-master
git init
```

## 2. Apply the patches

All at once:

```bash
git apply "$PATCHES"/*.patch
```

Or one at a time; each command creates one commit:

```bash
git apply "$PATCHES"/0001-*.patch
git apply "$PATCHES"/0002-*.patch
# ... and so on up to 0009
```

They must be applied in numerical order, without skipping any.

## 3. Check the result

```bash
git log --oneline        # should list 9 commits
ls -A                    # should show app.py, agents/, tools/, README.md and so on
```

## If something goes wrong

| What you see | What to do |
| --- | --- |
| `previous rebase directory .git/rebase-apply still exists` | An earlier `git apply` was interrupted. Run `git apply --abort`, then start again |
| `patch does not apply` | Usually the order is wrong, or the folder already contains a file with the same name. Run `git apply --abort`, make sure the folder is clean, then continue from the missing number |
| You want to start over | Delete the whole new folder and begin again from step 1 |

## A different folder layout

If the root of the git repository is the parent folder and `budget-master/` is only a subfolder of it, run this in the parent folder instead:

```bash
cd ~/some-folder
git init
git apply --directory=budget-master "$PATCHES"/*.patch
```

## Notes

- The patches do not contain `.env`, `.venv/` or `generated/`; those are never committed. After applying, set the environment up again:
  ```bash
  python3 -m venv .venv && source .venv/bin/activate
  pip install -r requirements.txt
  cp .env.example .env     # then add the API key
  ```
- `presentation.pptx` and `walkthrough.html` were added by two later commits and are not part of these 9 patches.
