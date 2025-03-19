# SlipDeck 🎴📦

SlipDeck is an open-source Python utility built specifically for Trading Card Game (TCG) sellers. Easily transform your order details from TCGPlayer into professional, 4x6-compatible packing slips, sorted pull sheets, and labels.

**Other markets like eBay, Mercari and PriceCharting coming soon!**

SlipDeck helps you save money and streamline your shipping process—saving you valuable time and effort!

Happy selling & collecting! 🎴✨

## Save Money 💰

By printing packing slips on 4x6 thermal paper, you'll significantly reduce costs associated with traditional inkjet printers. Thermal printing eliminates ink usage and greatly reduces paper waste, saving you money, boosting your bottom line and contributing to a more efficient, eco-friendly operation.

## Features ⚙️

- ✅ Generate clean, professional packing slips for TCG orders
- 🖨 Optimized for 4x6 label printers (thermal labels)
- 📑 Create organized pull sheets grouped by Game for easy order fulfillment
- 🎯 Compatible with popular TCG marketplaces (TCGPlayer, etc.)
- 📚 Multi-page order compatible

## Installation 💻

SlipDeck can be installed easily via pip:

```bash
pip install slipdeck
```

After installation, SlipDeck is simple to use from your terminal:

```bash
slipdeck --help
```

## Getting Started 🚀

1. Set your company name as an environment variable:

   ```bash
   export SLIPDECK_COMPANY_NAME="Your TCG Shop Name"
   ```

2. Download your packing slips from TCGPlayer:

   - Select the orders you want to process
   - Click on **Packing Slip** and select **Print Default**
   - Save the generated PDF file

3. Process your orders with SlipDeck:
   ```bash
   slipdeck /path/to/your/TCGplayer_PackingSlips.pdf
   ```

Your packing slips and pull sheets will be generated automatically!

## Contributing 🤝

We welcome contributions! Feel free to open issues, suggest features, or submit pull requests.

### Development

For local development:

```bash
pip install -e .
```

If you'd like to add a new dependency:

```bash
pip install pip-tools
pip-compile requirements.in --output-file requirements.txt
pip-sync requirements.txt
```

## License

MIT
