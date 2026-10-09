# wilayas

Algeria's 69 wilayas and 1,541 communes as a free, read-only JSON API, built from the official texts published in the Journal officiel.

> **Status: in development.** The first version is due by 30 November 2026, with [djazair.dev](https://github.com/djazairdev/djazair.dev).

## What it will serve

- **The 69 wilayas**, with their codes, Arabic and French names and chef-lieux.
- **The 1,541 communes**, with the wilaya each one belongs to.
- **The 2026 changes**: Law 26-06 of 4 April 2026 created 11 wilayas (59 to 69) and moved 108 communes into them. The parent wilayas run the new ones until 31 December 2026 at the latest. The API gives the old and the new wilaya of each moved commune, with the dates.
- **A citation for every record**: the text, its Journal officiel issue and the article it comes from.

The API is a set of static, versioned files in JSON and CSV. There are no keys and no sign-up, and any website can call it.

## Sources

- Law 84-09 of 4 February 1984 on the territorial division of the country, as amended, most recently by Law 26-06 of 4 April 2026 (Journal officiel n° 25 of 5 April 2026).
- Presidential Decree 26-206 of 25 May 2026 (Journal officiel n° 40 of 3 June 2026), which names and numbers the new wilayas.
- Ordinance 97-14 of 31 May 1997 (Journal officiel n° 38 of 4 June 1997), which moved 24 communes of Boumerdès, Tipaza and Blida to Algiers.
- Executive Decree 91-306 of 24 August 1991 (Journal officiel n° 41 of 4 September 1991), which lists the communes of each daïra.
- Executive Decree 21-198 of 11 May 2021 (Journal officiel n° 38 of 20 May 2021), which rewrites those lists for the 18 wilayas Law 19-12 changed or created.
- Executive Decree 26-253 of 15 July 2026 (Journal officiel n° 52 of 21 July 2026), which rewrites those lists for the 21 wilayas Law 26-06 changed or created.
- The code géographique national of ONS, the statistics office (June 2021), for the commune codes.

This is not an official government service.

## Licences

- Data: [CC0 1.0](LICENSE-data). Use it for anything, no permission needed.
- Code: [MIT](LICENSE).

Part of [djazair.dev](https://github.com/djazairdev).
