# Deep Extension

Extends the base EO protocol with features introduced in the Endless Online 0.3.x "deep" client series. These are **optional** updates — servers and players are free to adopt them independently of one another.

Official implementation guide: https://www.endless-online.com/deep/techinfo.html ([Archived](https://web.archive.org/web/20250327014424/https://www.endless-online.com/deep/techinfo.html))

## Changes

### New packet families / actions

| Addition | Value |
|---|---|
| `PacketFamily::Boss` | 52 |
| `PacketFamily::Captcha` | 249 |
| `PacketAction::Config` | 220 |
| `PacketAction::Swap` | 35 |

### Extended enums

| Enum | Change |
|---|---|
| `AccountReply` | `WrongPin = 8` added |
| `AvatarChangeType` | `Skin = 4`, `Gender = 5` added |
| `ItemType` | `Reserved5 → Transformation`, `Reserved7 → Spell`, `Reserved8 → Document`, `Reserved26 → Buff`, `Reserved27 → Debuff`, `Reserved28 → Title`, `Reserved29 → HairTool` |

### New enums

| Enum | Description |
|---|---|
| `AccountValidationReply` | Result codes for emailed PIN-code validation during account creation |
| `AccountRecoverReply` | Result codes for the password recovery account-lookup step |
| `AccountRecoverPinReply` | Result codes for the password recovery PIN-verification step |
| `AccountRecoverUpdateReply` | Result codes for the password recovery new-password step |
| `LookupType` | Entity type for `#item` / `#npc` lookup commands |

### New structs / extended structs

| Struct | Description |
|---|---|
| `DialogLine` | One row of a Communications dialog (left string + right string) |
| `AvatarChange` *(extended)* | Added `Skin` and `Gender` switch cases |

### New server packets

| Packet | Description |
|---|---|
| `Account::Config` | Account creation delay time and email validation flag |
| `Account::Accept` | Reply to email PIN-code validation |
| `Login::Config` | Max skins, hair modals, and character name length for character creation |
| `Login::Take` | Reply to "forgot password?" — opens recovery screen |
| `Login::Create` | Reply to account name submission for recovery |
| `Login::Accept` | Reply to recovery PIN submission |
| `Login::Agree` | Reply to new password submission |
| `Boss::Ping` | Boss NPC HP broadcast |
| `Captcha::Open` | Show captcha popup (server-checked or client-checked mode) |
| `Captcha::Agree` | Update captcha popup with a new challenge |
| `Captcha::Close` | Close captcha popup and award experience |
| `AdminInteract::Create` | Open a new Communications info dialog |
| `AdminInteract::Add` | Append lines to an open Communications dialog |
| `Paperdoll::Swap` | Equip-swap result with full paperdoll stats update |

### Extended server packets

| Packet | Added fields |
|---|---|
| `Barber::Open` | `max_hair_styles`, `base_cost`, `cost_per_level` |

### New client packets

| Packet | Description |
|---|---|
| `Account::Accept` | Submit emailed PIN-code to complete account validation |
| `Login::Take` | "Forgot password?" button click |
| `Login::Create` | Submit account name for password recovery |
| `Login::Accept` | Submit 7-digit recovery PIN code |
| `Login::Agree` | Submit new password (with account name and PIN) |
| `Captcha::Reply` | Submit captcha answer |
| `Captcha::Request` | Request a new captcha after too many failures |
| `Item::Report` | Submit a new title string via a title certificate (item type 28) |
| `AdminInteract::Take` | `#item` / `#npc` pub lookup |
