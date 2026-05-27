# Context Prior to This Log

## Context

This should be the only log written in past tense, as this is a commentary about the check-in system as it was at the time I joined the team (although I'm writing this a couple of months later).

The code was stored in a single repository and was deployed using git clone directly to the check-in kiosks stationed in the Makerspace, the Basement, and the SIO Makerspace. This raised several security concerns (detail intentionally omitted). The environment the check-in process ran in was quite chaotic, as the kiosks (running Raspbian) had several untracked scripts and assorted python venvs with a variety of packages haphazardly installed, presumably from the prior few years of technical debt accumulated as no procedures had been put in place to deploy the system from scratch.

As for the actual check-in system, there were also several questionable practices in play: most files were contained in just 2 directories, the UI was written in vanilla tkinter, the check in flow was implemented quite unintuitively (with combinatorial logic around the user's account and waiver status), and several other organizational and structural issues.

Motivated by this, I decided it would be worthwhile to rewrite a majority of the system. I anticipate this will likely cause me pain in the short term dealing with the inevitable bugs that pop up, but I believe it will be worth it in the end to eliminate a lot of the technical debt (surely this won't come back to haunt me). I hope this documentation of the major decisions I've made can help you provide context for decisions made in the future.

-Timothy Washburn