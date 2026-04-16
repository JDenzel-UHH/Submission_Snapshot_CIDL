# CIDL — Access Configuration (S3)

This document explains how to configure **read-only S3 access** for the datasets used by **CIDL**.

Access to the University of Hamburg’s **Cloudian S3** storage is required because all datasets are hosted there.  
Without valid permission files (`config` and `credentials`), you will not be able to download or stream any data.

---

## 1) Request access

To obtain access, request the CIDL S3 access files via email (ls.statistik.bwl@uni-hamburg.de).

You will receive two files:
- `config`
- `credentials`

These files are set up for the AWS profile with the **Profile name** `cidl-readonly` (do not rename)

---

## 2) What you will receive

After your request is approved, you will receive **two plain-text files**:

### `config`
The `config` file defines:
- the AWS **profile** (`cidl-readonly`)
- the **S3 endpoint** (the Cloudian host, i.e., an S3-compatible endpoint)
- S3 client settings (e.g., **path-style addressing**)

### `credentials`
The `credentials` file contains the **access keys** for the same profile:
- `aws_access_key_id`
- `aws_secret_access_key`

This profile is **read-only**. You can list and download objects that you have permission for, but you cannot upload or modify data.

### Important consistency rule
The profile name must match across both files:
- In the `config` file, the profile is referenced as `profile cidl-readonly`
- In the `credentials` file, the profile is referenced as `cidl-readonly`

Do not change the profile name in either file.

---

## 3) Where to place the files (.aws directory)

CIDL expects the access files in a folder named .aws inside your user home directory.

**Note**: This folder is often hidden and may need to be made visible first.

The two files must be placed there and must be named exactly:

- `config`
- `credentials`

### macOS

Target folder:
- ~/.aws/

Full target paths:
- ~/.aws/config
- ~/.aws/credentials

What ~ means: ~ is your personal home directory
on macOS, this usually means: /Users/your-username/

**Steps**:

1. Open Finder
2. In the top menu, click Go
3. Click Go to Folder...
4. Enter: ~/.aws
5. Press Enter
6.1 if the folder opens, copy the provided files into it
6.2 if the folder does not exist yet, create a folder named exactly .aws inside your home directory and then place the files there

Important: .aws begins with a dot because it is a hidden folder. If you do not see hidden folders, press Shift + Command + . in Finder to show them


### Linux

Target folder:
- ~/.aws/

Full target paths:
- ~/.aws/config
- ~/.aws/credentials

What ~ means: ~ is your personal home directory
on Linux, this usually means: /home/your-username/

**Steps**:
1. Open your file manager
2. Navigate to your Home folder
3. Show hidden files and folders
4. on most systems, press Ctrl + H
5. Look for a folder named .aws
6.1 if the folder exists, open it and copy the provided files into it
6.2 if it does not exist, create a new folder named exactly .aws inside your home directory and place the files there

### Windows

Target folder:
- %UserProfile%\.aws\

Full target paths:
- %UserProfile%\.aws\config
- %UserProfile%\.aws\credentials

**Steps**:
1. Press Win + R
2. Enter: %UserProfile%\.aws
3. Press Enter
4. Then:
5.1 if the folder opens, copy the provided files into it
5.2 if the folder does not exist, create it and then place the files there

Common Windows pitfall:

make sure the files are not accidentally saved as config.txt or credentials.txt

#### Final check

After copying the files, your .aws folder should contain exactly these two files:

- config
- credentials

CIDL will read these files from your home directory when establishing the connection.

---

## 4) Using the correct profile

If you already have multiple S3 profiles on your machine, ensure that the profile used for CIDL access is:

- `cidl-readonly`

How you select the profile depends on your setup:
- Some workflows use the environment variable `AWS_PROFILE`.
- Some libraries/tools allow specifying a profile explicitly (recommended when available).

If CIDL provides a `profile` option, prefer setting it explicitly to `cidl-readonly` to avoid ambiguity.

---

## 5) Verify access

To verify your setup, you can run the repository quickstart:

- [Quickstart](https://github.com/JDenzel-UHH/CIDL/blob/main/example/Quickstart.py)

If configuration is correct, the script should be able to reach the storage backend and load at least one dataset/truth file without authentication errors.

---

## 6) Key rotation (important)

Access keys may be **rotated periodically**.

Typical symptoms:
- access worked previously but suddenly fails
- errors like “access denied” or “invalid access key”

Fix:
- request **new** `credentials` (and, also a refreshed `config`)
- replace your local files in `~/.aws/` with the new versions

---

## 7) Security notes

- **Never commit** `credentials` (or any secrets) to git.
- Do not paste keys into notebooks, scripts, or issue trackers.
- Store keys only in your local AWS config directory (`~/.aws/`).

---

## 8) Troubleshooting (common issues)

### Profile not found
Symptoms:
- errors indicating the profile `cidl-readonly` does not exist

Checks:
- confirm both files exist in the `.aws` directory
- confirm the profile name is exactly `cidl-readonly` in both files
- confirm `config` is placed in the correct location and is not named `config.txt`

### No credentials found
Symptoms:
- errors indicating missing credentials

Checks:
- confirm `credentials` exists and is readable
- confirm the file is in the correct `.aws` directory (especially on Windows)

### Access denied / suddenly stops working
Checks:
- keys may have rotated → request new credentials
- confirm you are using the correct profile (`cidl-readonly`)

### Cannot connect to endpoint
Checks:
- verify network connectivity

---

## 9) Support

If setup still fails, contact the maintainer/chair contact and include (do **not** include any secret keys):
- your OS (Windows/macOS/Linux)
- the exact error message
- confirmation that `config` and `credentials` exist (paths only)
- whether you have multiple AWS profiles configured
