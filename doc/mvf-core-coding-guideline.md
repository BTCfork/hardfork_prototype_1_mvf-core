# MVF-Core coding guideline

## Introduction

This document describes some of the coding guidelines that contributors to MVF-Core should follow.

First of all, we need to keep in mind that MVF-Core is a fork of Bitcoin Core, and code may be merged in either direction or into other Bitcoin clients.
For that reason, we should try to follow the general rules/conventions that apply to Satoshi-derived Bitcoin clients, and for the MVF-Core we should follow Core-compatible coding rules.

The last thing we want to do is argue about coding conventions. So if you have a question or suggestion, let's discuss it before you submit that huge Pull Request, and we'll get it sorted out beforehand and adapt these guidelines where necessary.
Contact us on #dev on <https://btcforks.slack.com> .


## Related documents

Some of the general rules and those formulated by Core are documented in the following files in this doc/ folder:

[ TODO: list the files and what info they contain that should be paid attention to: ]

1. developer-notes.md: general coding rules applicable to Bitcoin Core
2. TODO: filename - description of what important rules it contains
3. TODO: filename - description of what important rules it contains
...


## MVF-Core repositories and branching model

This section will describe how to submit pull requests, based on the branches in use on the MVF repo(s).
Not directly coding related, but it's relevant to the process of getting code submitted and we don't have another document better suited yet.

To be completed.


## Marking code changes

### Copyrights

Suggested we use the 'The Bitcoin developers' for BTCfork related work.
Where necessary add to the copyright messages, or create a new one.
Do not remove existing attribution.

### Changing legacy code sections

Add a marker comment that shows that the section has been changed by MVF-Core.
A suitable comment format for single-line changes:

    // MVF-Core: some change description

For multi-line sections, it is often impractical/counterproductive  to add
such a comment on each changed line.

In those cases a begin/end format can be used, e.g.

    // MVF-Core begin: some change description (include req/design id!)
    ... ( changed code section)
    // MVF-Core end


## Commit messages / PR descriptions

This is also not directly coding related, but will make everyone's life
easier if we stick to some conventions.

What follows are draft proposals, and subject to change as we move along.
But let's try implementing them.


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

If the commit is just non-issue related development work, please include
the identifier of a requirement or design element that this relates to,
and make sure that the requirement or design element is included in
a comment near code which you've changed.

    implemented safe client shutdown for wallet backup failure (MVHF-CORE-SW-REQ-10-5)


## General Bitcoin coding rules

To be completed if there is anything that still needs to be said that is not in the referenced docs e.g. developer-notes.md.



## MVF-Core-specific rules (added by BTCfork)

1. Code changes need to traceable back to design. In general, only things that are described in the design document should be coded up. If they're not, make sure you ask why they're not in the design document.  Maybe they just need to be added. Or maybe there's not even requirements for them, in case that needs changing first. Raise GH issues where necessary.

[ TODO: example of how to trace design element in the actual code. ]

2. To be completed.

