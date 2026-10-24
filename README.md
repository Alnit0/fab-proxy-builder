# FAB Proxy Order Builder

A single-page tool for putting together Flesh and Blood proxy orders for MakePlayingCards.

Type card names (or paste a decklist), pick the art, set quantities, and download one zip. The zip holds print-ready images with bleed and a `fab-order.xml` order file for the [MPC Autofill](https://github.com/chilli-axe/mpc-autofill) desktop tool, which fills in the MakePlayingCards order for you.

## Using it

Open the site, add cards, click **Download order (.zip)**, then follow the steps on the page.

## Files

| File | What it is |
| --- | --- |
| `index.html` | The whole tool, with the card list built in |
| `cardback.jpg` | The default card back (Fakes and Bootleg) |
| `tools/` | Scripts to rebuild `index.html` with a fresh card list |

## Updating the card list

The page has a **Check for new cards** link that pulls the latest list in the browser. To bake a newer list into `index.html` instead:

```bash
git clone --depth 1 https://github.com/the-fab-cube/flesh-and-blood-cards.git
python3 tools/make_index.py flesh-and-blood-cards/json/english tools/cards.json
cd tools && python3 assemble.py YYYY-MM-DD ../index.html
```

Use the card data's last update date for `YYYY-MM-DD`.

## Credits

- Card data: [the-fab-cube/flesh-and-blood-cards](https://github.com/the-fab-cube/flesh-and-blood-cards)
- Card images: [Fabrary](https://fabrary.net)
- Order automation: [MPC Autofill](https://github.com/chilli-axe/mpc-autofill)

Flesh and Blood is a trademark of Legend Story Studios. This is an unofficial fan tool for personal playtesting.
