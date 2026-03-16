# coauthorcheck Action

Marketplace-ready GitHub Action for validating `Co-authored-by` trailers with `coauthorcheck`.

This repository is meant to be published separately from the main `coauthorcheck` Python package repo because GitHub Marketplace actions work best from a dedicated public repository with a root `action.yml`.

## Usage

```yaml
steps:
  - uses: actions/checkout@v4
    with:
      fetch-depth: 0

  - name: Validate branch commits
    uses: simoncraf/coauthorcheck-action@v0.1.0
    with:
      package-version: "0.6.0"
      range: origin/main..HEAD
```

## Inputs

- `range`: required git revision range to validate
- `config`: optional config file path
- `format`: optional output format, `text` or `json`
- `python-version`: optional Python version used inside the action
- `package-version`: optional PyPI package version to install
- `working-directory`: optional working directory for running `coauthorcheck`
- `comment-on-pr`: optional, set to `true` to create or update a PR comment
- `comment-mode`: optional, `failures-only` or `always`
- `delete-comment-on-success`: optional, delete the existing PR comment after a successful run
- `github-token`: optional token for PR comment operations
- `comment-header`: optional markdown heading for the PR comment

When `comment-on-pr` is enabled, the action forces JSON internally even if `format: text` is requested.

## Outputs

- `status`: `pass`, `fail`, or `error`
- `exit-code`: raw `coauthorcheck` exit code
- `issue-count`: total validation issue count
- `invalid-commit-count`: number of commits with issues
- `warning-count`: total warning count
- `comment-action`: `created`, `updated`, `deleted`, or `none`

## Example Workflows

Validate commits introduced by a pull request:

```yaml
name: Validate Co-authored-by trailers on PR

on:
  pull_request:
    branches:
      - main

jobs:
  validate-commits:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      pull-requests: write

    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Validate PR commits
        uses: simoncraf/coauthorcheck-action@v0.1.0
        with:
          package-version: "0.6.0"
          range: origin/${{ github.base_ref }}..HEAD
          comment-on-pr: "true"
          comment-mode: failures-only
```

Validate commits introduced by branch pushes:

```yaml
name: Validate Co-authored-by trailers

on:
  push:
    branches:
      - "feature/**"
      - "feat/**"

jobs:
  validate-commits:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Validate branch commits
        uses: simoncraf/coauthorcheck-action@v0.1.0
        with:
          package-version: "0.6.0"
          range: origin/main..HEAD
```

## Comment behavior

The action uses a single hidden marker to manage one PR comment:

```html
<!-- coauthorcheck-comment -->
```

Behavior:

- validation failures create or update the managed comment
- successful runs delete the managed comment when `delete-comment-on-success` is `true`
- comment operations on non-PR events are skipped with a workflow warning

## Permissions

- `contents: read`
- `pull-requests: write` when `comment-on-pr: "true"`
