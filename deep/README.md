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
| `AccountConfig` | Account creation delay time and email validation flag |
| `AccountAccept` | Reply to email PIN-code validation |
| `LoginConfig` | Max skins, hair modals, and character name length for character creation |
| `LoginTake` | Reply to "forgot password?" — opens recovery screen |
| `LoginCreate` | Reply to account name submission for recovery |
| `LoginAccept` | Reply to recovery PIN submission |
| `LoginAgree` | Reply to new password submission |
| `BossPing` | Boss NPC HP broadcast |
| `CaptchaOpen` | Show captcha popup (server-checked or client-checked mode) |
| `CaptchaAgree` | Update captcha popup with a new challenge |
| `CaptchaClose` | Close captcha popup and award experience |
| `AdminInteractCreate` | Open a new Communications info dialog |
| `AdminInteractAdd` | Append lines to an open Communications dialog |
| `PaperdollSwap` | Equip-swap result with full paperdoll stats update |

### Extended server packets

| Packet | Added fields |
|---|---|
| `BarberOpen` | `max_hair_styles`, `base_cost`, `cost_per_level` |

### New client packets

| Packet | Description |
|---|---|
| `AccountAccept` | Submit emailed PIN-code to complete account validation |
| `LoginTake` | "Forgot password?" button click |
| `LoginCreate` | Submit account name for password recovery |
| `LoginAccept` | Submit 7-digit recovery PIN code |
| `LoginAgree` | Submit new password (with account name and PIN) |
| `CaptchaReply` | Submit captcha answer |
| `CaptchaRequest` | Request a new captcha after too many failures |
| `ItemReport` | Submit a new title string via a title certificate (item type 28) |
| `AdminInteractTake` | `#item` / `#npc` pub lookup |
