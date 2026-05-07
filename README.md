# boastermelt

Attempts to RE the LiteOn/PLDS `DS-8ABSH` DVD drive.

Initially inspired by the epic [coastermelt](https://scanlime.org/tag/coastermelt/)

For a blog post on this, see [here](https://johnowhitaker.dev/posts/dvd_hack.html)

For a minimal readme to start hacking on this project, see [here](https://github.com/johnowhitaker/bmelt/blob/codex/clean-slate/minimal/README.md) (in minimal/)

This repo has the tricks we've worked out so far: dumping and decrypting the firmware, running the firmware update process, patching a helper to allow modified firmware by working around the integrity check, reading out memory from currentboot, recovering from a few scary-looking states. It also has a ton of mess from (so far unsuccessful) attempts to get past the next blocker: decoding the CDDs to gain full normal-mode control of the drive and its functions.

USE AT OWN RISK, I'VE BRICKED A FEW DRIVES ALREADY :)

LMK if you have any questions, I don't expect this to be useful to anyone but I will be pleasantly surprised if it does.
