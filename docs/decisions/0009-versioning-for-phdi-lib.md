# 9. Formalize software version numbers using Semantic Versioning (SemVer)

Date: 2022-6-28

## Status

Accepted

## Context and Problem Statement

As the PHDI building blocks software continues to develop, documenting the versions that the software goes through will become increasingly important. Users will need to be able to track released versions of the software to ensure that they're using the correct version for their use cases, and so that they can receive proper support in the event they experience a software problem. Developers need to be able to document introductions of new features and bug fixes in existing features. Software versioning allows both groups to avoid confusion around the state of PHDI building blocks library.

## Decision Drivers

* **Transparency**: The adopted versioning should clearly convey relevant information about the software, such as the presence or absence of major features as well as the presence or absence of particular fixes.
* **Consistency**: The adopted versioning should communicate that two identically-versioned instances of the software should behave identically; in other words, version X of the software on one machine should have the exact same characteristics as version X of the software on a different machine.
* **Interpretability**: The adopted versioning should be easily interpretable to both a user and a developer. Users should be able to tell at a glance what version of the software they are using, and they should be able to understand the differences between two similarly-versioned instances of the software.

## Considered Options

1. **Name Versioning**
  - Defined as versioning that uses names of objects in some category to take the place of major versions of the software.
  - Examples: NATO alphabet for air traffic codes; Apple's use of large felines (and now desert environments) for operating systems
  - Pros:
    * Each name is highly memorable and clearly differentiates large versions being discussed
    * Names should achieve some degree of consistency
  - Cons:
    * Unrelated names do not convey information about major or minor features, or bug fixes, that may be present in the software
    * Doesn't allow for small changes, such as bug fixes, without tooling an entirely new name
    * Cannot be clearly interpreted to convey differences in two versions without a likely long release notes document
2. **Date-of-release Versioning**
  - Defined as versioning marked simply by the standard date on which the version was released
  - Examples: Anaconda package manager
  - Pros:
    * Achieves consistency by being precise about the exact version achieved
    * Highly interpretable by virtue of dates
  - Cons:
    * Prone to "version verbosity" that becomes hard to separate from one another--did that bug fix patch come out on the 16th or the 17th?
    * No clear relationship between aspects of the version numbers that are changing and what's changing in the software--in fact, it may artificially create the notion that there's a predefined monthly major release schedule
3. **Sequential Number Versioning**
- Defined as versioning that begins with "1" and increments the count with each successive software push
- Examples: Not really any that work out in the wild
- Pros:
  * Largely the same as date-of-release versioning without the drawback of an imposed / artificial schedule
- Cons:
  * Also susceptible to version verbosity, as with date versioning
  * The optics of a massively large number for a version number (i.e. 427) could reduce confidence in our ability to make correct software the first time
  * Creates the temptation to not increment the version number to avoid the above problem, which then eliminates consistency as well
4. **Semantic Versioning (SemVer)**
- Defined as versioning of the form A.B.C. _A_ corresponds to the "major release" number and documents the addition, alteration, or removal of features sufficient to break the existing API. _B_ corresponds to the "minor release" number and documents the addition or removal of features which _do not_ break the existing API. _C_ corresponds to the "patch version" and documents the bug fixes that have been applied to the software.
- Examples: All of Google's internal and external software platforms; the R kernel
- Pros:
  * Achieves transparency by clearly delineating when an aspect of the software changes, as well as showing what that aspect was
  * Achieves consistency by separating out breaking vs non-breaking API changes
  * Achieves interpretability by adding a "patch version" to MAJOR.MINOR versioning schemes, which conveys whether particular bugs have been fixed or not
  * Well-documented, formally used process that reduces ambiguity on the developer side, to the extent that many major software developers around the world use it
  * Optics around version numbers make intuitive sense to users; in other words, they should "feel natural" in a world where things like e.g. operating system numbers are of the form 14.12.21, which allows developers to create lots of changes and alter the version number without creating the feeling of an unstably changing software platform
- Cons:
  * May require careful consideration and discussion around whether a change has actually "broken" the existing API
  * Bug fix / patch number can sometimes be treated as a "catch all" bucket and wind up spiraling to large numbers like sequential number versioning

## Decision Outcome

We are adopting Semantic Versioning to document the PHDI building blocks library's development. It is robust, standardized, and well-documented with precise protocols for when things change and what those changes should be. It will achieve all three major decision drivers and provide additional clarity for both users and developers.

## Appendix

The full specification of SemVer can be found (here)[https://semver.org/]
