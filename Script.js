$(document).ready(function () {
    initCompanySearch();
    initClearFilters();
    initPaymentStatusToggle();
    initFormValidation();
});

function initCompanySearch() {
    $('#customer_name').on('input', function () {
        var term = $(this).val();
        if (term.length > 0) {
            $.getJSON('/api/companies', { term: term }, function (data) {
                $('#company-list').empty();
                $.each(data, function (index, company) {
                    $('#company-list').append('<a href="#" class="list-group-item list-group-item-action">' + company + '</a>');
                });
            });
        } else {
            $('#company-list').empty();
        }
    });

    $(document).on('click', '.list-group-item', function (e) {
        e.preventDefault();
        $('#customer_name').val($(this).text());
        $('#company-list').empty();
    });
}

function initClearFilters() {
    $('#clear-filters').click(function () {
        console.log('Clear Filters button clicked');
        $('#customer_name').val('');
        $('#date').val('');
        $('#payment_term').val('');
        $('#company-list').empty();
        window.location.href = '/dashboard';
    });
}

function initPaymentStatusToggle() {
    $('select[name*="payment_status"]').change(function () {
        toggleFields(this);
    });

    function toggleFields(selectElement) {
        const $row = $(selectElement).closest('tr');
        const paymentStatus = $(selectElement).val();
        const $evidenceInput = $row.find("input[type='file']");
        const $expectedDateInput = $row.find("input[type='date']");
        const $partialPaymentCell = $row.find('.partial-payment-cell');

        if (paymentStatus === 'Paid') {
            $evidenceInput.prop('disabled', true);
            $expectedDateInput.prop('required', true);
            $partialPaymentCell.hide();
        } else if (paymentStatus === 'Partial Payment') {
            $evidenceInput.prop('disabled', false);
            $expectedDateInput.prop('required', false);
            $partialPaymentCell.show();
        } else {
            $evidenceInput.prop('disabled', false);
            $expectedDateInput.prop('required', false);
            $partialPaymentCell.hide();
        }
    }
}

function initFormValidation() {
    $('form').on('submit', function (e) {
        const rows = $(this).find('tbody tr');
        let valid = true;

        rows.each(function () {
            const paymentStatus = $(this).find('select[name*="[payment_status]"]').val();
            const followUpDate = $(this).find('input[name*="[follow_up_date]"]').val();

            if (paymentStatus === 'Unpaid' && !followUpDate) {
                valid = false;
                alert('Please select a Follow-Up Date for unpaid invoices!');
                return false;
            }
        });

        if (!valid) {
            e.preventDefault();
        }
    });
}