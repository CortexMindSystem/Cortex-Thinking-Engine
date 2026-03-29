> [!IMPORTANT]
> Before using Fastlane for CortexOS, you must first clone the shared Fastlane configuration:
>
> `git clone https://github.com/CortexMindSystem/fastlane`
>
> or (SSH):
>
> `git clone git@github.com:CortexMindSystem/fastlane.git`
>
> Then, copy the `Appfile` and `Fastfile` from the cloned repository into your local `CortexOSApp/fastlane/` directory:
>
> cp fastlane/Appfile CortexOSApp/fastlane/
> cp fastlane/Fastfile CortexOSApp/fastlane/

----

fastlane documentation
----

# Installation

Make sure you have the latest version of the Xcode command line tools installed:

```sh
xcode-select --install
```

For _fastlane_ installation instructions, see [Installing _fastlane_](https://docs.fastlane.tools/#installing-fastlane)

# Available Actions

### ios_testflight

```sh
[bundle exec] fastlane ios_testflight
```

iOS TestFlight (alias)

### mac_testflight

```sh
[bundle exec] fastlane mac_testflight
```

macOS TestFlight (alias)

### all_testflight

```sh
[bundle exec] fastlane all_testflight
```

Build and upload BOTH platforms to TestFlight

----


## iOS

### ios testflight_release

```sh
[bundle exec] fastlane ios testflight_release
```

Build iOS and upload to TestFlight

----


## Mac

### mac testflight_release

```sh
[bundle exec] fastlane mac testflight_release
```

Build macOS and upload to TestFlight

----

# CortexOS Fastlane Setup

This directory contains Fastlane configuration files for automated iOS and macOS builds and TestFlight deployment.

- `Appfile` — App Store Connect and team configuration (never commit secrets)
- `Fastfile` — Build and deployment lanes

See the main project README for usage instructions.

This README.md is auto-generated and will be re-generated every time [_fastlane_](https://fastlane.tools) is run.

More information about _fastlane_ can be found on [fastlane.tools](https://fastlane.tools).

The documentation of _fastlane_ can be found on [docs.fastlane.tools](https://docs.fastlane.tools).
