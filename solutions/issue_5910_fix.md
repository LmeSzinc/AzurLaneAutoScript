**Patch – `ui.py` (core UI handling)**  
The bug is caused by the script mis‑detecting the *Settings* page after a delegated task is started.  
We add a dedicated handler that tries to recover from this state by clicking the back button or, if that fails, by forcing a restart.  
The handler is called from `ensure_page()` before any normal navigation logic runs.

```diff
--- a/ui.py
+++ b/ui.py
@@
     def