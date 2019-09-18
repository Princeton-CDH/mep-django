/*
 * Code refactored to support ES6 imports; see original:
 * https://github.com/tristen/tablesort/blob/gh-pages/src/sorts/tablesort.number.js
 *
 * See also this issue: https://github.com/tristen/tablesort/issues/169
 */
const cleanNumber = (i: string) =>  i.replace(/[^\-?0-9.]/g, '')

const compareNumber = (a: string, b: string) => {
    let numberA = parseFloat(a)
    let numberB = parseFloat(b)

    numberA = isNaN(numberA) ? 0 : numberA
    numberB = isNaN(numberB) ? 0 : numberB

    return numberA - numberB
}

const prefixedCurrencyRe = /^[-+]?[£\x24Û¢´€]?\d+\s*([,\.]\d{0,2})/
const suffixedCurrencyRe = /^[-+]?\d+\s*([,\.]\d{0,2})?[£\x24Û¢´€]/
const numberRe = /^[-+]?(\d)*-?([,\.]){0,1}-?(\d)+([E,e][\-+][\d]+)?%?$/

export const sortItem = (item: string) => {
    return item.match(prefixedCurrencyRe) ||
           item.match(suffixedCurrencyRe) ||
           item.match(numberRe)
}

export const compareItem = (a: string, b: string) => {
    a = cleanNumber(a)
    b = cleanNumber(b)
    return compareNumber(b, a)
}
