# MVF-Core coding guideline

## Introduction

This document describes some of the coding guidelines that contributors to
MVF-Core should follow.

First of all, we need to keep in mind that MVF-Core is a fork of Bitcoin
Core, and in future code may need to be merged in either direction or into
other Bitcoin clients.
For that reason, we should try to follow the general rules/conventions
that apply to Satoshi-derived Bitcoin clients, and for the MVF-Core we should
follow Core-compatible coding rules.

The last thing we want to do is argue about coding conventions. So if you
have a question or suggestion, let us discuss it before you submit that
huge Pull Request, and we will get it sorted out beforehand and adapt
these guidelines where necessary. Please contact us on the #dev channel on
<https://btcforks.slack.com> to discuss.


## Related documents

Some of the general rules and those formulated by Core are documented in the
following files in this doc/ folder:

1. developer-notes.md: general coding rules and some guidelines for
   Bitcoin (and therefore MVF-Core too)

[ TODO: list any additional files and what info they contain that should
be paid attention to: ]


## MVF-Core repositories and branching model

The original repository at <https://github.com/BTCfork/hardfork_prototype_1_mvf-core>
is considered the main development repository for now.

If you want to develop, please clone from there or fork this repository
on GitHub.

The default development branch is `master`.

You should always branch off `master` in your own repo before doing some
development. Branch off into a feature branch if your development is
going to implement a new feature, or a hotfix branch if you are going to
fix an issue.

Branch naming convention in your own forked repo is your business,
but please make sure that you follow the commit message and PR naming
conventions laid out in further sections.

The following table gives an overview of the branches in the main repo
and their purpose.


| Branch name  | Purpose of branch                                     |
| ------------ |------------------------------------------------------ |
| master       | Main development and integration branch. Pull requests should be made relative to this branch. |
| 0.12         | Vendor branch - tracks upstream work on Core 0.12. No MVF development takes place here. It exists only so that MVF-Core can be more easily rebased onto latest Core 0.12 changes. |


## Marking code changes

More important than code markers are accurate commit messages.
However, the MVF-Core development will use code markers to help them
with identifying its changes.

Ensure that changes are marked unless it is absolutely not possible
for technical reasons (some files simply do not allow it, it is
forgivable in those cases.


### Copyrights

Suggested we use the `The Bitcoin developers` for BTCfork related work.
Where necessary add to the copyright messages, or create a new one.
Do not remove existing attribution.


### Changing legacy code sections

Add a marker comment that shows that the section has been changed by MVF-Core.
A suitable comment format for single-line changes:

    // MVF-Core: some change description

For multi-line sections, it is often impractical/counterproductive to add
such a comment on each changed line.

In those cases a begin/end format can be used, e.g.

    // MVF-Core begin: some change description (include req/design id!)
    ... ( changed code section)
    // MVF-Core end


## Commit messages / PR descriptions

This is also not directly coding related, but will make all our lives
easier if we stick to some conventions.

What follows are draft proposals, and subject to change as we move along.
We will try to keep changes minimal however.

Think about whether a change you are making can be adequately expressed
by the conventions below.

If not, contact us before you commit, so that we can potentially extend
the guidelines as you need. This will make the end result more consistent.


### Commit messages

These should contain a brief description on the first line.
There can be other paragraphs giving more details.

If a commit or PR is only about documentation, like this document, then
it should be prefixed by `[doc]`, e.g:

    [doc] update the coding guideline

For regression tests (qa/ folder) it should be prefixed by `[qa]`, e.g.

    [qa] add a test for MVHF-CORE-SW-REQ-x-y

If the commit is addressing a GitHub issue for the project,
then the first line (description) should reference the Issue number. If
this needs to be combined with other prefixes, the square bracket tags
should go in front, like this:

    [doc] Issue#123: correct the installation manual

A `[bld]` tag should be used for matters related to the build system,
packaging scripts or templates files, gitian descriptors or any
interfacing related to external continuous integration (CI) systems:

    [bld] Issue#444: add a specfile for building on CentOS

If a commit is solely non-issue related development work, please include
the identifier of a requirement or design element that this relates to,
and make sure that the requirement or design element is included in
a comment near code which you have changed.

    safe client shutdown for wallet backup failure (MVHF-CORE-SW-REQ-10-5)


### Pull requests (PRs)

All PRs should be made against the `master` branch of `BTCfork/hardfork_prototype_1_mvf-core` .

Where a PR is simple enough to be described by a single prefix tag like
`[doc]`, `[qa]` or `[bld]`, the title of the PR should contain this prefix.

For more complex PRs (which is typically the case), the title description
should contain an identifier such as an Issue# (like for commits) if the
PR covers a single task.


## General Bitcoin coding rules

To be completed if there is anything that still needs to be said that is
not in the referenced docs e.g. developer-notes.md.



## MVF-Core-specific rules (added by BTCfork)

1. Code changes need to traceable back to design. In general, only things
   that are described in the design document should be coded up. If they
   are not, make sure you ask why they are not in the design document.
   Maybe they just need to be added. Or maybe there are not even
   requirements for them, in which case that needs changing first.
   Raise GH issues where necessary.

   Example of tracing back to a design element from a code change:

   `strClient = "Bitcoin MVF-Core client";  // MVF-Core client name (MVHF-CORE-DES-IDME-1)`

   Please participate to make the design complete and precise where you
   want to make a change that is not presently described.

   In the final review we will look at all code changes and check that
   they are traceable.

2. We use specifically `// MVF-Core` tags to mark MVF changes .

   This should generally be completed with some description of the change,
   preferably citing the associated design element (preferably) or requirement.

3. Existing comments should be preserved if possible.

