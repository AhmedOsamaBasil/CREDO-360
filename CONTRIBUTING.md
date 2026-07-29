# Contributing

Bug reports, reproducibility reports, and focused pull requests are welcome.

1. Open an issue describing the controller, configuration, seed, platform, and
   observed behavior.
2. Create a branch from `main`.
3. Keep experimental claims paired with the raw per-seed output and the exact
   configuration used to generate it.
4. Run both test suites before opening a pull request:

   ```bash
   python -m pytest testbed/tests -q
   python live_testbed/test_portable.py
   ```

5. Do not commit participant-identifiable data, credentials, copyrighted video
   segments, or packet captures that cannot legally be redistributed.

Contributions are accepted under the repository's MIT license.

