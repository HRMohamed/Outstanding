document.addEventListener('DOMContentLoaded', function () {
    // Toggle fields based on the selected status
    window.toggleFields = function (selectElement, invoiceId, balance) {
        const status = selectElement.value;
        const paidAmount = document.getElementById(`paid-amount-${invoiceId}`);
        const remainingAmount = document.getElementById(`remaining-amount-${invoiceId}`);
        const paymentDate = document.getElementById(`payment-date-${invoiceId}`);
        const expectedDate = document.getElementById(`expected-date-${invoiceId}`);

        // Reset fields
        paidAmount.disabled = true;
        remainingAmount.value = balance.toFixed(2);
        paymentDate.disabled = true;
        expectedDate.disabled = true;

        // Enable based on status
        if (status === 'Partial Payment') {
            paidAmount.disabled = false;
            expectedDate.disabled = false;
        } else if (status === 'Paid') {
            paymentDate.disabled = false;
        } else if (status === 'Unpaid') {
            expectedDate.disabled = false;
        }
    };

    // Calculate remaining balance
    window.calculateRemaining = function (paidAmountInput, invoiceId, balance) {
        const paidAmount = parseFloat(paidAmountInput.value) || 0;
        const remainingAmount = Math.max(balance - paidAmount, 0);
        document.getElementById(`remaining-amount-${invoiceId}`).value = remainingAmount.toFixed(2);
    };

    // Validate the form before submission
    window.validateForm = function () {
        let valid = true;
        const rows = document.querySelectorAll('tbody tr');

        rows.forEach(row => {
            const status = row.querySelector('select').value;
            const paidAmount = row.querySelector('input[name^="paid_amount"]');
            const paymentDate = row.querySelector('input[name^="payment_date"]');
            const expectedDate = row.querySelector('input[name^="expected_date"]');

            if (status === 'Partial Payment') {
                if (!paidAmount.value || !expectedDate.value) {
                    alert(`Please fill Paid Amount and Expected Payment Date for Invoice ID: ${row.id.split('-')[1]}`);
                    valid = false;
                }
            } else if (status === 'Paid') {
                if (!paymentDate.value) {
                    alert(`Please fill Payment Date for Invoice ID: ${row.id.split('-')[1]}`);
                    valid = false;
                }
            }
        });

        return valid;
    };
});
