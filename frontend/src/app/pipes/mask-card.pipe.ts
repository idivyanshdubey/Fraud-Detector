import { Pipe, PipeTransform } from '@angular/core';

@Pipe({
  name: 'maskCard'
})
export class MaskCardPipe implements PipeTransform {
  transform(cardNumber: string): string {
    if (!cardNumber) return '';
    
    // Handle different card number formats
    if (cardNumber.includes('-')) {
      // Format: 4532-1234-5678-9012
      const parts = cardNumber.split('-');
      if (parts.length === 4) {
        return `****-****-****-${parts[3]}`;
      }
    } else if (cardNumber.length === 16) {
      // Format: 4532123456789012
      return `**** **** **** ${cardNumber.slice(-4)}`;
    }
    
    // Default masking for any other format
    const visibleLength = Math.min(4, cardNumber.length);
    const maskedLength = Math.max(0, cardNumber.length - visibleLength);
    return '*'.repeat(maskedLength) + cardNumber.slice(-visibleLength);
  }
}
