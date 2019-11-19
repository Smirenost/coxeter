# Change Log
The format is based on
[Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to
[Semantic Versioning](http://semver.org/spec/v2.0.0.html).

## next

### Added

* Continuous integrated testing on CircleCI.

### Changed

* Moved core shape classes from euclid.FreudShape into top-level package namespace.
* Shapes from Damasceno science 2012 paper are now stored in a JSON file that is loaded in the damasceno module.

### Fixed

* Formatting now properly follows PEP8.

### Removed

* Various unused or redundant functions in the utils module.
* The quaternion\_tools module (uses rowan for quaternion math instead).
* Remove shapelib.

## v0.1.0

* Initial version of code base.
