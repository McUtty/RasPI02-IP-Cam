# Synchronizing the Project with GitHub

Follow these steps on your Raspberry Pi (or any machine with git access) to push the current project state to a GitHub repository.

1. **Ensure git knows who you are**
   ```bash
   git config --global user.name "Your Name"
   git config --global user.email "you@example.com"
   ```

2. **Add a GitHub remote**
   Replace `<github-username>` and `<repository>` with your repository path:
   ```bash
   git remote add origin git@github.com:<github-username>/<repository>.git
   ```
   If the remote already exists, update it instead:
   ```bash
   git remote set-url origin git@github.com:<github-username>/<repository>.git
   ```

3. **Fetch the latest changes**
   ```bash
   git fetch origin
   ```

4. **Ensure you are on the branch you want to push**
   ```bash
   git checkout work
   ```

5. **Merge or rebase as needed**
   ```bash
   git merge origin/work
   ```
   Or, if you prefer rebasing:
   ```bash
   git rebase origin/work
   ```

6. **Push your local commits to GitHub**
   ```bash
   git push -u origin work
   ```

After running these commands your local `work` branch will be synchronized with the remote GitHub repository.
