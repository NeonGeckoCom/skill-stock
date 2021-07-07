# <img src='https://0000.us/klatchat/app/files/neon_images/icons/neon_skill.png' card_color="#FF8600" width="50" style="vertical-align:bottom">Stock

## Summary

This skill provides stock values.

## Requirements

No special required packages for this skill.

## Description

Use this skill to lookup stock prices


## Examples

* what is * trading at
* what is the stock price for *

## Location

    ${skills}/stock.neon

## Files

    stock.neon/requirements.txt
    stock.neon/__pycache__
    stock.neon/__pycache__/__init__.cpython-36.pyc
    stock.neon/vocab
    stock.neon/vocab/en-us
    stock.neon/vocab/en-us/company.entity
    stock.neon/vocab/en-us/StockPrice.intent
    stock.neon/README.md
    stock.neon/regex
    stock.neon/regex/en-us
    stock.neon/regex/en-us/company.rx
    stock.neon/__init__.py
    stock.neon/test
    stock.neon/test/intent
    stock.neon/test/intent/stock.price2.intent.json
    stock.neon/test/intent/stock.price1.intent.json
    stock.neon/dialog
    stock.neon/dialog/en-us
    stock.neon/dialog/en-us/stock.price.dialog
    stock.neon/dialog/en-us/not.found.dialog
    stock.neon/settings.json
    stock.neon/LICENSE


  

## Class Diagram

[Click Here](https://0000.us/klatchat/app/files/neon_images/class_diagrams/translation.png)

## Available Intents
<details>
<summary>Show list</summary>
<br>

### company.entity  
    ... 
      
### StockPrice.intent  
    what is the stock price for {company}
    what is the stock price of {company}
    what is the share price for {company}
    what is the share price of {company}
    what is {company} trading at

</details>  

## Details

### Text

        what is the stock price for Microsoft
        >> Microsoft Corp, with ticker symbol MSFT is currently trading at 125.44 dollars per share. 

        what is Sonos trading at
        >> Sonos Inc, with ticker symbol SONO is currently trading at 11.25 dollars per share.

### Picture

### Video

  

## Contact Support

Use the [link](https://neongecko.com/ContactUs) or [submit an issue on GitHub](https://help.github.com/en/articles/creating-an-issue)

## Credits

reginaneon MycroftAI djmcknight358 [neongeckocom](https://neongecko.com/)

