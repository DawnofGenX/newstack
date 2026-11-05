<?php

use App\Http\Controllers\StatController;
use Illuminate\Support\Facades\Route;

Route::get('/', [StatController::class, 'service']);
Route::match(['get', 'post'], '/count', [StatController::class, 'count']);
