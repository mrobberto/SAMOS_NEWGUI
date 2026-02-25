SAMOS Software Release Procedure
################################

In order to keep the repository consistent, and in sync with the software on the WS, this 
document describes the release procedures to be used.

Goals
*****

These procedures are intended to ensure the following:

- The github repository matches the code on the WS unless one or the other is actively 
  being worked on.
- After work is done on either the repository or WS, the two are brought back into
  agreement as soon as possible.
- We don't have a bunch of branches around on the repository where it's not clear which
  one(s) have work being done, or what work is being done in the branch.
- When looking at a branch, it's clear what the branch is intended to do
- We keep separate changes in separate branches, so that if one is easy and another turns 
  out to be hard, we can get the easy one merged in while working on the hard one
- We avoid having multiple versions of the SAMOS directory on the WS, without a clear idea
  of what their differences are, and why they have those differences.
- Make sure we have 2 pairs of eyes (minimum) on any repository change
- In the SAMOS directory on the WS, we have 3 possible "src" directories:

  - "src" holds the code that will run if you start SAMOS
  - "src_testing" holds the current code being tested right now
  - "src_working" holds the code that we want to run when doing observations

Merge Procedure
***************

After creating and committing a branch, create a pull request and ask for reviews. If you
receive a request for review, look at the code as soon as possible. Having at least a 
second pairs of eyes on the code change is extremely helpful.

The converse to this is that pull requests should be as small as possible. Especially, 
keep files that are not relevant to the changes you made out of the pull request. Any
ephemeral changes (e.g. current DMD position, target planning region files) should not be
added to the repository unless there's a reason that they need to be a part of the code.

After Making Changes on the WS During Observation
*************************************************

In this case, it's important to get the repository to reflect the current code running on
the WS. As such,

1. On the WS, zip the "src" directory inside the SAMOS code. Copy that zip file to your
   local machine. Then immediately delete it from the server.
2. If you don't have a clean copy of the repository, clone the SAMOS repository and check
   out the "main" branch.
3. Create a new branch in the form "observation_<DATE>_code_updates" using the git command
   `git checkout -b BRANCH`
4. Unzip the "src" directory from the WS, and replace the "src" directory in your
   repository with this directory.
5. Run `git status` on the repository. If there are any untracked files that need to be
   added to the repository, add them.
6. Run `git commit -a -m "MESSAGE"` with MESSAGE describing the changes you made.
7. Run `git push`
8. On the github website, create a pull request from the new branch to main, and request
   at least one other SAMOS person to review the pull request.
9. Once the pull request has been approved, merge it in right away, and delete the branch.

Fixing Bugs or Issues in the Repository
***************************************

In this case, we want to make sure the changes are understandable, and we want to make 
sure that they are added to the WS before the next observations are taken.

1. Create a new branch on the repository. For the branch name, _describe the specific 
   changes that you are making in this branch_. The fewer changes, the better. For
   example, if the issue is that the up-arrow button isn't working properly, a branch name 
   like "fix_up_arrow_button_main_tab" would be good, and any other changes can (and 
   should) be put in a different branch (using this same procedure for it).
2. Immediately commit and push the changes, and create a pull request to add them to main.
3. Once the PR has been approved, merge it and then delete the branch.
4. make sure that your local repository reflects the changes.
5. Compress the "src" directory from your repository, and copy it to the WS.
6. Replace the "src" directory on the WS with your new copy
7. Delete the zipped src directory.

Making Upgrades or Enhancements
*******************************

In this case, the work might take some time to complete, so it's important to make sure 
that it stays up-to-date with any other changes that are being made.

1.  Create a new branch describing the upgrade. For example, adding SAMI control to the
    GUI might be "upgrade_add_sami_control"
2.  Do enough work to make a commit and push the branch to the repository.
3.  Create a pull request _and mark it as a draft_
4.  Continue work, remembering:

    - If you are making other changes to the repository, remember to update the working
      branch so it has those changes added.
    - Commit and push your local changes often
    - If you need to do work not related to the upgrade, _do it in another branch_ as per
      one of the other procedures above.

5.  When you have finished the work, test it. If you need to test it on the WS,

    - Compress the "src" directory, and copy it to the WS
    - _Rename_ the existing WS "src" directory to "src_working"
    - Add the testing "src" directory to the SAMOS code on the WS, and delete the 
      compressed version
    - Run your tests
    - If there is an existing "src_testing" directory, delete it
    - Rename the "src" directory to "src_testing"
    - Rename the "src_working" directory to "src"

6.  As soon as the PR is approved, merge it in to main, and delete the branch.
7.  Compress the "src" directory from your repository, and copy it to the WS.
8.  Replace the "src" directory on the WS with your new copy
9.  Delete the zipped src directory.
10. Delete the "src_testing" directory (if present) on the WS
