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

The card list updates itself. A GitHub Action (`.github/workflows/update-cards.yml`) runs every morning, rebuilds the list from Fabrary's card data, and republishes `index.html` if any cards changed. To run it straight away, open the **Actions** tab, choose **Update card list**, then **Run workflow**.

To rebuild by hand:

```bash
npm pack @flesh-and-blood/cards --ignore-scripts && tar xzf flesh-and-blood-cards-*.tgz
git clone --depth 1 https://github.com/the-fab-cube/flesh-and-blood-cards.git fabcube
python3 tools/fabrary_index.py package/dist/cards.js /tmp/fabrary.json
python3 tools/make_index.py fabcube/json/english /tmp/fabcube.json
python3 tools/merge_lists.py /tmp/fabrary.json /tmp/fabcube.json tools/cards.json
cd tools && python3 assemble.py YYYY-MM-DD ../index.html
```

## Credits

- Card data: [Fabrary](https://github.com/fabrary/cards), with event cards from [the-fab-cube/flesh-and-blood-cards](https://github.com/the-fab-cube/flesh-and-blood-cards)
- Card images: [Fabrary](https://fabrary.net)
- Order automation: [MPC Autofill](https://github.com/chilli-axe/mpc-autofill)

Flesh and Blood is a trademark of Legend Story Studios. This is an unofficial fan tool for personal playtesting.
