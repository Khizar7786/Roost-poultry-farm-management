# Publish the application and models

Use one GitHub repository for application source and one Hugging Face model
repository for the price bundle. This guide does not create accounts,
repositories, or deployments automatically.

## Included and excluded files

Commit backend `.py` source, migrations, tests, requirements, frontend
source/assets/configuration, `package.json`, `package-lock.json`, docs,
environment examples, `LICENSE`, and `NOTICE`.

The root `.gitignore` excludes virtual environments including `venv_old`,
`node_modules`, build output, real `.env` files, SQLite databases,
uploads, runtime logs/PIDs, model artifacts, and the raw training CSV.
These exclusions preserve the files locally. Keep database backups outside
the repository; a public source repository must not contain registered
accounts or their password hashes.

## Before the first push

1. Configure your replacement Roboflow key outside source code and revoke
   the previously shared key in your Roboflow account.
2. Run the checks in the [root README](../README.md#automated-checks).
3. Review the [Apache 2.0 license](../LICENSE) and [NOTICE](../NOTICE).
   Dependencies, datasets, and externally hosted models retain their own terms.
4. Publish and document a complete model bundle following [MODELS.md](MODELS.md).
   Use a private model repository until its redistribution terms are established.

## GitHub upload

Create an empty GitHub repository without an automatically generated README,
license, or `.gitignore`. From the application repository root:

```powershell
git init
git branch -M main
git add .
git status --short
git diff --cached --stat
git diff --cached
```

Inspect the staged files for credentials, account data, local uploads,
installed packages, and model artifacts before continuing. Then replace
the placeholder repository URL and upload:

```powershell
git commit -m "Initial Roost FYP source"
git remote add origin https://github.com/Khizar7786/Roost-poultry-farm-management.git
git push -u origin main
```

If the directory is already a Git repository, inspect `git status` and
`git remote -v` and use its existing history and remote rather than repeating
initialization. `.gitignore` does not remove files already tracked in Git.
Exposed credentials must be revoked/rotated even if a later commit removes them.

## Automated checks on GitHub

`.github/workflows/ci.yml` runs on pushes and pull requests with read-only
repository permissions. It installs Python 3.11 backend dependencies and
runs Django checks, migration consistency, and the API suite. A second job
installs frontend dependencies with `npm ci` and builds with Node 22.

The checks require no model download or service credentials. They do not
publish artifacts or deploy the application. The first hosted CI result
will be available after you push this repository to GitHub.

Uploading code and model artifacts is separate from deploying the frontend
and Django backend as a publicly accessible website.

## References

- [GitHub Python CI](https://docs.github.com/en/actions/tutorials/build-and-test-code/python)
- [Credential exposure guidance](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository)
- [Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0)
